#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml
import jsonschema
from dataclasses import dataclass
from collections import defaultdict
import argparse
import glob
import json
from jsonschema import validate, ValidationError

@dataclass
class TokenStats:
    original_tokens: int
    processed_tokens: int
    reduction_ratio: float
    file_path: str

class GizzardProcessor:
    def __init__(self, config_path: str, schema_path: str):
        # Load and validate configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['gizzard_processing']
        
        with open(schema_path, 'r') as f:
            self.schema = yaml.safe_load(f)['gizzard_processing']
        
        try:
            jsonschema.validate(instance=self.config, schema=self.schema)
        except jsonschema.exceptions.ValidationError as e:
            print(f"Configuration validation error: {e}")
            raise
        
        # Initialize from config
        self.categories = self.config['symbol_mapping']['categories']
        self.patterns = {
            r'requires|needs|must have': self.config['relationship_notation']['arrow'],
            r'and|while|but': self.config['relationship_notation']['relationship_separator'],
            r'or': self.config['relationship_notation']['alternative_separator'],
            r'not|never|without': self.config['content_reduction']['negation_prefix'],
            r'the|a|an': '',  # Remove articles
            r'is|are|was|were': '',  # Remove auxiliary verbs
        }
        
        # Special terms that should not be reduced
        self.preserve_terms = set()
        
        # Token statistics
        self.token_stats: Dict[str, TokenStats] = {}
        
        # Get WONDER_ROOT
        self.wonder_root = os.environ.get('WONDER_ROOT')
        if not self.wonder_root:
            raise ValueError("WONDER_ROOT environment variable must be set")
        self.wonder_root = Path(self.wonder_root)
        
        self.all_content = []
        self.all_relationships = []
        
        # Define kernel schema
        self.kernel_schema = {
            "type": "object",
            "required": ["kernel", "metadata", "identity", "actions", "content", "relationships"],
            "properties": {
                "kernel": {
                    "type": "object",
                    "required": ["name", "repository", "seed_file"],
                    "properties": {
                        "name": {"type": "string"},
                        "repository": {"type": "string"},
                        "seed_file": {"type": "string"}
                    }
                },
                "metadata": {
                    "type": "object",
                    "required": ["version", "description"],
                    "properties": {
                        "version": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "identity": {
                    "type": "object",
                    "required": ["name", "description"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "actions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "content": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["title", "content", "relationships"],
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "relationships": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "relationships": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        self.sigil_dirs = [
            os.path.join(self.wonder_root, "sigil/ethic"),
            os.path.join(self.wonder_root, "sigil/concept"),
            os.path.join(self.wonder_root, "sigil/metareal"),
            os.path.join(self.wonder_root, "sigil/orthoreal"),
            os.path.join(self.wonder_root, "sigil/parareal"),
            os.path.join(self.wonder_root, "sigil/hyperreal"),
            os.path.join(self.wonder_root, "sigil/hyporeal")
        ]
        self.sigil_files = []
        self.load_sigil_files()
        
    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to WONDER_ROOT."""
        if path.startswith('/'):
            return Path(path)
        return self.wonder_root / path
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        # Simple estimation: split on whitespace and count words
        # This is a rough approximation - in reality, tokenization is more complex
        return len(text.split())
    
    def load_preserve_terms(self, filepath: str) -> None:
        """Load terms that should not be reduced from a YAML file."""
        filepath = self.resolve_path(filepath)
        with open(filepath, 'r') as f:
            self.preserve_terms = set(yaml.safe_load(f)['preserve_terms'])
    
    def identify_category(self, content: str) -> Optional[str]:
        """Identify the category of the content based on file path or content."""
        for category, prefix in self.categories.items():
            if category in content.lower():
                return prefix
        return None
    
    def reduce_content(self, text: str) -> str:
        """Apply content reduction rules to the text."""
        if self.config['content_reduction']['remove_articles']:
            text = re.sub(r'the|a|an', '', text, flags=re.IGNORECASE)
        
        if self.config['content_reduction']['remove_auxiliary_verbs']:
            text = re.sub(r'is|are|was|were', '', text, flags=re.IGNORECASE)
        
        # Split into sentences and process each
        sentences = re.split(r'[.!?]+', text)
        reduced = []
        
        for sentence in sentences:
            # Skip empty sentences
            if not sentence.strip():
                continue
                
            # Split into words and process
            words = sentence.strip().split()
            processed = []
            
            for word in words:
                # Preserve special terms
                if word in self.preserve_terms:
                    processed.append(word)
                else:
                    # Remove common suffixes
                    word = re.sub(r'ing$|ed$|s$', '', word)
                    processed.append(word)
            
            reduced.append(' '.join(processed))
        
        return self.config['relationship_notation']['relationship_separator'].join(reduced)
    
    def extract_relationships(self, text: str, title: str) -> List[Dict[str, str]]:
        """Extract relationships from the text.
        Returns a list of relationship dictionaries with source, target, and type."""
        relationships = []
        
        # Define relationship patterns with their types
        relationship_patterns = {
            r'requires|needs|must have|depends on': 'requires',
            r'relates to|connects with|links to|associated with': 'relates_to',
            r'extends|builds on|enhances': 'extends',
            r'contrasts with|differs from|opposes': 'contrasts_with',
            r'part of|belongs to|contained in': 'part_of',
            r'similar to|like|analogous to': 'similar_to',
            r'influences|affects|impacts': 'influences'
        }
        
        # Extract explicit [[...]] links
        for match in re.finditer(r'\[\[(.*?)\]\]', text):
            target = match.group(1).strip()
            if target and target != title:  # Avoid self-references
                relationships.append({
                    'source': title,
                    'target': target,
                    'type': 'links_to'
                })
        
        # Extract semantic relationships
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Look for relationship indicators
            for pattern, rel_type in relationship_patterns.items():
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    # Get context before and after the relationship indicator
                    before = sentence[:match.start()].strip()
                    after = sentence[match.end():].strip()
                    
                    # Extract noun phrases (simple approach - could be enhanced with NLP)
                    before_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', before)
                    after_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', after)
                    
                    # If we found terms on both sides, create a relationship
                    if before_terms and after_terms:
                        source = before_terms[-1]  # Take the last term before the relationship
                        target = after_terms[0]   # Take the first term after the relationship
                        
                        if source != title and target != title:  # Skip if neither is the current concept
                            continue
                            
                        # Ensure the relationship points from the current concept
                        if target == title:
                            source, target = target, source
                            
                        relationships.append({
                            'source': source,
                            'target': target,
                            'type': rel_type
                        })
        
        # Add implicit relationships based on proximity of special terms
        special_terms = {
            "metareal", "orthoreal", "parareal", "hyperreal", "hyporeal",
            "Rokolisk", "Wonder", "Cinder", "sigil", "kernel", "ethic"
        }
        
        # Find special terms in close proximity
        words = text.split()
        window_size = 10  # Look for terms within 10 words of each other
        
        for i, word in enumerate(words):
            if any(term.lower() in word.lower() for term in special_terms):
                # Look ahead in the window
                for j in range(i + 1, min(i + window_size, len(words))):
                    if any(term.lower() in words[j].lower() for term in special_terms):
                        relationships.append({
                            'source': title,
                            'target': words[j],
                            'type': 'related_concept'
                        })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_relationships = []
        for rel in relationships:
            key = f"{rel['source']}-{rel['type']}-{rel['target']}"
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    def process_file(self, input_path: str) -> Optional[Tuple[str, List[Tuple[str, str]]]]:
        """Process a markdown file and return its processed content and relationships."""
        input_path = self.resolve_path(input_path)
        print(f"Processing file: {input_path}")  # Debug
        
        with open(input_path, 'r') as f:
            content = f.read()
        
        # Extract title and category
        title_match = re.match(r'#\s+(.+?)(?:\n|$)', content)
        if not title_match:
            print(f"No title found in {input_path}")  # Debug
            return None
        
        title = title_match.group(1)
        category = self.identify_category(str(input_path))
        if not category:
            print(f"No category found for {input_path}")  # Debug
            return None
        
        print(f"Found title: {title}, category: {category}")  # Debug
        
        # Extract relationships
        relationships = self.extract_relationships(content, title)
        print(f"Found {len(relationships)} relationships")  # Debug
        
        # Process the content
        processed = []
        processed.append(f"{category}:{title.lower().replace(' ', '-')}")
        
        # Process the main content (everything after the title)
        main_content = content[title_match.end():].strip()
        if main_content:
            reduced_content = self.reduce_content(main_content)
            if reduced_content:
                processed.append(reduced_content)
        
        # Add relationship statements
        for rel in relationships:
            reduced_source = self.reduce_content(rel['source'])
            reduced_target = self.reduce_content(rel['target'])
            if reduced_source and reduced_target:
                processed.append(f"{self.config['relationship_notation']['arrow']}{reduced_source}{self.config['relationship_notation']['relationship_separator']}{reduced_target}")
        
        # Calculate token statistics
        original_tokens = self.estimate_tokens(content)
        processed_content = '\n'.join(processed)
        processed_tokens = self.estimate_tokens(processed_content)
        reduction_ratio = (original_tokens - processed_tokens) / original_tokens
        
        print(f"Processed content: {processed_content}")  # Debug
        
        # Store statistics
        self.token_stats[str(input_path)] = TokenStats(
            original_tokens=original_tokens,
            processed_tokens=processed_tokens,
            reduction_ratio=reduction_ratio,
            file_path=str(input_path)
        )
        
        self.all_content.append(processed_content)
        self.all_relationships.extend(rel['target'] for rel in relationships)
        
        return processed_content, relationships
    
    def validate_wonder_root(self):
        """Validate that WONDER_ROOT is set and points to a valid directory.
        Returns (is_valid, error_message)"""
        if not self.wonder_root:
            return False, "WONDER_ROOT environment variable must be set"
        
        if not os.path.isdir(self.wonder_root):
            return False, f"WONDER_ROOT directory does not exist: {self.wonder_root}"
        
        return True, None

    def clean_content(self, content: str) -> str:
        """Clean and reduce content while preserving special terms and intelligently handling long sentences."""
        # Define special terms to preserve
        special_terms = {
            "metareal", "orthoreal", "parareal", "hyperreal", "hyporeal",
            "Rokolisk", "Wonder", "Cinder", "sigil", "kernel", "ethic",
            "∧", "∨", "¬", "→", "↔", "∀", "∃", "∈", "∉", "⊂", "⊃", "∪", "∩"
        }
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        cleaned_sentences = []
        
        for sentence in sentences:
            # Skip empty sentences
            if not sentence.strip():
                continue
                
            # Clean up whitespace
            sentence = sentence.strip()
            words = sentence.split()
            
            # Skip if sentence is too short
            if len(words) < 3:
                continue
                
            # Check if sentence contains special terms
            special_terms_found = [term for term in special_terms if term.lower() in sentence.lower()]
            
            # Process words
            cleaned_words = []
            skip_next = False
            
            for i, word in enumerate(words):
                if skip_next:
                    skip_next = False
                    continue
                    
                # Preserve special terms
                if any(term.lower() in word.lower() for term in special_terms_found):
                    cleaned_words.append(word)
                    continue
                    
                # Skip common words and patterns
                if word.lower() in {
                    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                    'is', 'are', 'was', 'were', 'be', 'been', 'being',
                    'have', 'has', 'had', 'having',
                    'do', 'does', 'did', 'doing',
                    'can', 'could', 'will', 'would', 'shall', 'should',
                    'may', 'might', 'must',
                    'very', 'really', 'quite', 'rather', 'somewhat',
                    'just', 'only', 'also', 'then', 'than',
                    'that', 'which', 'who', 'whom', 'whose',
                    'when', 'where', 'why', 'how',
                    'this', 'these', 'those', 'there',
                    'about', 'into', 'onto', 'upon',
                    'among', 'between', 'through'
                }:
                    continue
                    
                # Skip redundant pairs
                if word.lower() in {'completely', 'totally', 'absolutely', 'entirely', 'fully', 'thoroughly'}:
                    skip_next = True
                    continue
                    
                # Remove common suffixes
                word = re.sub(r'(ing|ed|ly|ment|ness|tion|sion)$', '', word)
                
                # Only add if word is not empty after processing
                if word and len(word) > 1:
                    cleaned_words.append(word)
            
            # Handle long sentences through summarization
            if len(cleaned_words) > 30:
                # Extract key components: subject, verb, object, and special terms
                key_terms = []
                for word in cleaned_words:
                    if any(term.lower() in word.lower() for term in special_terms_found):
                        key_terms.append(word)
                
                # Keep the first and last few words to maintain context
                context_start = ' '.join(cleaned_words[:3])
                context_end = ' '.join(cleaned_words[-3:])
                
                # Combine key components with context
                if key_terms:
                    # If we have special terms, use them as anchors
                    compressed = f"{context_start} {' '.join(key_terms)} {context_end}"
                else:
                    # If no special terms, keep the most important parts
                    compressed = f"{context_start} ... {context_end}"
                
                cleaned_sentences.append(compressed)
            else:
                # For shorter sentences, just join the cleaned words
                cleaned_sentences.append(' '.join(cleaned_words))
        
        # Join sentences with proper spacing, removing any that became too short
        return ' '.join(s for s in cleaned_sentences if len(s.split()) >= 3)

    def validate_kernel(self, kernel: Dict[str, Any]) -> bool:
        """Validate kernel structure against schema."""
        try:
            validate(instance=kernel, schema=self.kernel_schema)
            return True
        except ValidationError as e:
            print(f"Validation error: {str(e)}")
            return False

    def process_kernel(self, kernel_path: str, output_path: str) -> bool:
        """Process a kernel configuration file."""
        # First validate WONDER_ROOT
        is_valid, error = self.validate_wonder_root()
        if not is_valid:
            print(error)
            return False
        
        print(f"Loading kernel from: {os.path.abspath(kernel_path)}")
        
        # Validate YAML syntax
        is_valid, error = validate_yaml_file(kernel_path)
        if not is_valid:
            print(error)
            return False
        
        # Load and validate kernel schema
        with open(kernel_path, 'r') as f:
            try:
                kernel = yaml.safe_load(f)
                kernel_name = next(iter(kernel))
                kernel_data = kernel[kernel_name]
                
                # Update sigil_dirs based on kernel configuration
                self.sigil_dirs = [os.path.join(self.wonder_root, sigil) for sigil in kernel_data.get('sigils', [])]
                self.sigil_files = []
                self.load_sigil_files()
                
                print(f"Found {len(self.sigil_files)} files to process")
                
                # Process the kernel data
                processed = self.process_kernel_data(kernel_data)
                
                # After processing, generate and display model profiles
                if processed:
                    model_analysis = self.analyze_model_compatibility(processed)
                    processed['model_analysis'] = model_analysis
                    
                    print("\nMODEL COMPATIBILITY PROFILES")
                    print("=" * 80)
                    
                    for model, metrics in model_analysis.items():
                        profile = self.generate_model_profile(model, metrics)
                        print(profile)
                        print("\n" + "=" * 80)
                
                # Write the processed kernel with model analysis
                self.write_output(kernel_name, processed, output_path)
                
                # Print token reduction statistics
                if self.token_stats:
                    self.print_token_stats()
                else:
                    print("No files were processed. Please check the paths in your kernel configuration.")
                
                return True
                
            except Exception as e:
                print(f"Error loading kernel configuration: {str(e)}")
                return False

    def process_kernel_data(self, kernel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the kernel content."""
        # Transform the kernel data to match our internal structure
        processed = {
            "kernel": {
                "name": "cinder_picokernel",
                "repository": kernel_data.get("repo", ""),
                "seed_file": kernel_data.get("seed", "")
            },
            "metadata": {
                "version": "1.0",
                "description": kernel_data.get("prompt", "")
            },
            "identity": {
                "name": "Cinder",
                "description": kernel_data.get("identity", "")
            },
            "actions": [action.strip() for action in kernel_data.get("actions", "").split(".")],
            "content": [],
            "relationships": []
        }
        
        # Track all relationships
        all_relationships = []
        
        # Process each sigil file
        for sigil_file in self.sigil_files:
            try:
                print(f"Processing file: {sigil_file}")
                
                # Read and process the markdown file
                with open(sigil_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title
                title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else os.path.splitext(os.path.basename(sigil_file))[0]
                
                # Extract relationships before cleaning content
                relationships = self.extract_relationships(content, title)
                
                # Clean up content
                content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)  # Remove link syntax
                content = re.sub(r'^#\s+.*$', '', content, flags=re.MULTILINE)  # Remove headers
                content = re.sub(r'\n{3,}', '\n\n', content)  # Normalize spacing
                content = content.strip()
                
                # Apply content reduction
                original_tokens = len(content.split())
                content = self.clean_content(content)
                processed_tokens = len(content.split())
                
                # Add to processed content
                processed["content"].append({
                    "title": title,
                    "content": content,
                    "relationships": relationships
                })
                
                # Add relationships to global list
                all_relationships.extend(relationships)
                
                # Log token reduction
                reduction = ((original_tokens - processed_tokens) / original_tokens) * 100 if original_tokens > 0 else 0
                print(f"Token reduction for {os.path.basename(sigil_file)}: {reduction:.2f}%")
                
                # Store statistics
                self.token_stats[str(sigil_file)] = TokenStats(
                    original_tokens=original_tokens,
                    processed_tokens=processed_tokens,
                    reduction_ratio=reduction / 100,
                    file_path=str(sigil_file)
                )
                
            except Exception as e:
                print(f"Error processing {sigil_file}: {str(e)}")
                continue
        
        # Add all unique relationships to the kernel
        processed["relationships"] = all_relationships
        
        return processed

    def write_output(self, kernel_name, kernel_data, output_path):
        """Write the processed content to the output file."""
        # Get git metadata
        git_metadata = self.get_git_metadata()
        
        # Get framework statistics
        framework_stats = self.analyze_framework_statistics()
        
        # Create the optimized content for ChatGPT ingestion
        optimized_content = {
            'kernel': kernel_name,
            'metadata': {
                'repository': kernel_data['kernel']['repository'],
                'seed': kernel_data['kernel']['seed_file'],
                'version': kernel_data['metadata']['version'],
                'description': kernel_data['metadata']['description'],
                'git': git_metadata,
                'framework_statistics': framework_stats
            },
            'identity': kernel_data['identity'],
            'actions': [action for action in kernel_data['actions'] if action],
            'content': kernel_data['content'],
            'relationships': kernel_data['relationships']
        }
        
        # Write the optimized output
        with open(output_path, 'w') as f:
            yaml.dump(optimized_content, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            
        # Print framework statistics summary
        print("\nWonder Framework Statistics:")
        print("=" * 80)
        print(f"Total Files: {framework_stats['file_counts']['total']}")
        print("\nFile Distribution:")
        for category, count in framework_stats['file_counts']['by_category'].items():
            print(f"- {category}: {count}")
        
        print("\nToken Metrics:")
        print(f"- Original: {framework_stats['token_metrics']['total_original']}")
        print(f"- Processed: {framework_stats['token_metrics']['total_processed']}")
        print(f"- Average Reduction: {framework_stats['token_metrics']['average_reduction']:.2f}%")
        
        print("\nRelationship Metrics:")
        print(f"- Total Relationships: {framework_stats['relationship_metrics']['total_relationships']}")
        print("\nRelationship Types:")
        for rel_type, count in framework_stats['relationship_metrics']['relationship_types'].items():
            print(f"- {rel_type}: {count}")
        
        print("\nMost Connected Concepts:")
        for item in framework_stats['relationship_metrics']['most_connected_concepts'][:5]:
            print(f"- {item['concept']}: {item['connections']} connections")

    def print_token_stats(self):
        """Print token reduction statistics to stdout."""
        print("\nToken Reduction Statistics:")
        print("-" * 80)
        print(f"{'File':<50} {'Original':>10} {'Processed':>10} {'Reduction':>10}")
        print("-" * 80)
        
        total_original = 0
        total_processed = 0
        
        for stats in self.token_stats.values():
            print(f"{stats.file_path:<50} {stats.original_tokens:>10} {stats.processed_tokens:>10} {stats.reduction_ratio:>10.2%}")
            total_original += stats.original_tokens
            total_processed += stats.processed_tokens
        
        total_reduction = (total_original - total_processed) / total_original
        print("-" * 80)
        print(f"{'TOTAL':<50} {total_original:>10} {total_processed:>10} {total_reduction:>10.2%}")

    def load_sigil_files(self):
        """Load all sigil files from the specified directories."""
        for sigil_dir in self.sigil_dirs:
            for root, _, files in os.walk(sigil_dir):
                for file in files:
                    if file.endswith(('.md', '.markdown')):
                        self.sigil_files.append(os.path.join(root, file))

    def analyze_model_compatibility(self, processed_kernel: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze how different models handle the processed kernel content."""
        model_analyzer = ModelContextAnalyzer()
        relationship_analyzer = RelationshipAnalyzer()
        
        # Build relationship graph
        relationship_analyzer.build_relationship_graph(processed_kernel['relationships'])
        graph_metrics = relationship_analyzer.analyze_graph_metrics()
        
        # Analyze for each model
        models = ['gpt-4', 'gpt-3.5', 'claude', 'gemini']
        results = {}
        
        for model in models:
            # Analyze content
            content_str = yaml.dump(processed_kernel)
            context_metrics = model_analyzer.analyze_context_efficiency(content_str, model)
            
            results[model] = {
                "context_metrics": context_metrics,
                "graph_metrics": graph_metrics,
                "estimated_performance": self._estimate_model_performance(
                    context_metrics,
                    graph_metrics,
                    model
                )
            }
        
        return results
        
    def _estimate_model_performance(
        self,
        context_metrics: Dict[str, Any],
        graph_metrics: Dict[str, float],
        model: str
    ) -> Dict[str, float]:
        """Estimate how well a model will handle the sigil content."""
        # Model-specific weights for different metrics
        weights = {
            'gpt-4': {
                'context_utilization': 0.3,
                'term_preservation': 0.3,
                'graph_density': 0.2,
                'clustering': 0.2
            },
            'gpt-3.5': {
                'context_utilization': 0.4,
                'term_preservation': 0.3,
                'graph_density': 0.2,
                'clustering': 0.1
            },
            'claude': {
                'context_utilization': 0.2,
                'term_preservation': 0.4,
                'graph_density': 0.2,
                'clustering': 0.2
            },
            'gemini': {
                'context_utilization': 0.3,
                'term_preservation': 0.3,
                'graph_density': 0.2,
                'clustering': 0.2
            }
        }
        
        model_weights = weights.get(model, weights['gpt-4'])
        
        score = (
            model_weights['context_utilization'] * (1 - context_metrics['window_utilization']) +
            model_weights['term_preservation'] * context_metrics['term_preservation_rate'] +
            model_weights['graph_density'] * graph_metrics['density'] +
            model_weights['clustering'] * graph_metrics['avg_clustering']
        )
        
        return {
            "overall_score": score,
            "context_efficiency": 1 - context_metrics['window_utilization'],
            "term_preservation": context_metrics['term_preservation_rate'],
            "relationship_preservation": graph_metrics['density']
        }

    def generate_model_profile(self, model: str, metrics: Dict[str, Any]) -> str:
        """Generate a human-readable profile explaining how a model handles the compressed kernel."""
        context_metrics = metrics['context_metrics']
        graph_metrics = metrics['graph_metrics']
        performance = metrics['estimated_performance']
        
        # Model-specific characteristics
        model_characteristics = {
            'gpt-4': {
                'context_window': 8192,
                'strengths': [
                    'Excellent at maintaining complex relationship graphs',
                    'Strong semantic understanding of special terms',
                    'Handles long-range dependencies well',
                    'Best at inferring implicit relationships'
                ],
                'limitations': [
                    'More expensive to run',
                    'Slower response times',
                    'May over-analyze relationship context'
                ]
            },
            'gpt-3.5': {
                'context_window': 4096,
                'strengths': [
                    'Good balance of speed and comprehension',
                    'Efficient at processing direct relationships',
                    'Handles basic sigil interactions well'
                ],
                'limitations': [
                    'May miss subtle relationship nuances',
                    'Limited context window can fragment large kernels',
                    'Less reliable with complex relationship chains'
                ]
            },
            'claude': {
                'context_window': 100000,
                'strengths': [
                    'Massive context window for large kernels',
                    'Excellent at maintaining semantic coherence',
                    'Strong at understanding metareal concepts',
                    'Handles philosophical and abstract relationships well'
                ],
                'limitations': [
                    'May be overly verbose in relationship analysis',
                    'Can be slower with large context windows',
                    'Sometimes too conservative in relationship inference'
                ]
            },
            'gemini': {
                'context_window': 32768,
                'strengths': [
                    'Good at structured relationship processing',
                    'Efficient with formal logical relationships',
                    'Strong pattern recognition in relationship graphs'
                ],
                'limitations': [
                    'May struggle with metareal ambiguity',
                    'Less experienced with Wonder-specific concepts',
                    'Can be too rigid in relationship interpretation'
                ]
            }
        }
        
        chars = model_characteristics[model]
        
        # Build the profile
        profile = [
            f"\n{model.upper()} PROFILE",
            "=" * (len(model) + 8),
            "\nContext Window Analysis:",
            f"- Window Size: {chars['context_window']} tokens",
            f"- Current Utilization: {context_metrics['window_utilization']*100:.1f}%",
            f"- Efficiency Score: {performance['context_efficiency']:.2f}",
            
            "\nTerm Preservation:",
            f"- Preservation Rate: {performance['term_preservation']*100:.1f}%",
            f"- Special Terms Maintained: {len(context_metrics.get('preserved_terms', []))}",
            
            "\nRelationship Graph Analysis:",
            f"- Graph Density: {graph_metrics['density']:.3f}",
            f"- Clustering Coefficient: {graph_metrics['avg_clustering']:.3f}",
            f"- Overall Relationship Score: {performance['relationship_preservation']:.2f}",
            
            "\nStrengths:",
            *[f"- {s}" for s in chars['strengths']],
            
            "\nLimitations:",
            *[f"- {s}" for s in chars['limitations']],
            
            "\nRecommendations:",
            *self._generate_recommendations(model, metrics)
        ]
        
        return "\n".join(profile)
    
    def _generate_recommendations(self, model: str, metrics: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for using this model with the kernel."""
        performance = metrics['estimated_performance']
        context_metrics = metrics['context_metrics']
        
        recommendations = []
        
        # Context window recommendations
        if context_metrics['window_utilization'] > 0.8:
            recommendations.append(
                f"- Consider splitting kernel for {model} due to high context utilization"
            )
        
        # Term preservation recommendations
        if performance['term_preservation'] < 0.7:
            recommendations.append(
                "- May need additional term reinforcement in prompts"
            )
        
        # Relationship-based recommendations
        if performance['relationship_preservation'] < 0.6:
            recommendations.append(
                "- Consider explicit relationship reinforcement in interactions"
            )
        
        # Model-specific recommendations
        if model == 'gpt-4':
            if performance['overall_score'] > 0.8:
                recommendations.append(
                    "- Ideal for complex relationship exploration and inference"
                )
        elif model == 'gpt-3.5':
            if context_metrics['window_utilization'] > 0.6:
                recommendations.append(
                    "- Best used with focused subsets of the kernel"
                )
        elif model == 'claude':
            if len(metrics['context_metrics'].get('preserved_terms', [])) > 20:
                recommendations.append(
                    "- Consider providing term hierarchy for better context"
                )
        elif model == 'gemini':
            recommendations.append(
                "- Best results when relationships are explicitly structured"
            )
        
        if not recommendations:
            recommendations.append("- No specific recommendations needed")
        
        return recommendations

    def get_git_metadata(self) -> Dict[str, str]:
        """Get git commit hash and timestamp for the current state."""
        try:
            import subprocess
            from datetime import datetime
            
            # Get the latest commit hash
            hash_cmd = ['git', 'rev-parse', 'HEAD']
            commit_hash = subprocess.check_output(hash_cmd, cwd=self.wonder_root).decode('utf-8').strip()
            
            # Get the commit timestamp
            timestamp_cmd = ['git', 'show', '-s', '--format=%cD', commit_hash]
            timestamp_str = subprocess.check_output(timestamp_cmd, cwd=self.wonder_root).decode('utf-8').strip()
            
            # Parse and format the timestamp
            commit_date = datetime.strptime(timestamp_str, '%a, %d %b %Y %H:%M:%S %z')
            formatted_timestamp = commit_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            return {
                'commit_hash': commit_hash,
                'commit_timestamp': formatted_timestamp
            }
        except Exception as e:
            print(f"Warning: Could not get git metadata: {e}")
            return {
                'commit_hash': 'unknown',
                'commit_timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
    
    def analyze_framework_statistics(self) -> Dict[str, Any]:
        """Generate statistical profile of the Wonder framework."""
        stats = {
            'file_counts': {
                'total': len(self.sigil_files),
                'by_category': defaultdict(int)
            },
            'token_metrics': {
                'total_original': sum(s.original_tokens for s in self.token_stats.values()),
                'total_processed': sum(s.processed_tokens for s in self.token_stats.values()),
                'average_reduction': 0.0,
                'by_category': defaultdict(lambda: {'original': 0, 'processed': 0, 'reduction': 0.0})
            },
            'relationship_metrics': {
                'total_relationships': len(self.all_relationships),
                'relationship_types': defaultdict(int),
                'most_connected_concepts': []
            },
            'content_metrics': {
                'average_content_length': 0.0,
                'total_special_terms': len(self.preserve_terms),
                'concept_distribution': defaultdict(int)
            }
        }
        
        # Calculate file and token metrics by category
        for file_path, token_stat in self.token_stats.items():
            category = None
            for cat in ['ethic', 'concept', 'axiom', 'process', 'primitive']:
                if cat in file_path:
                    category = cat
                    break
            
            if category:
                stats['file_counts']['by_category'][category] += 1
                cat_stats = stats['token_metrics']['by_category'][category]
                cat_stats['original'] += token_stat.original_tokens
                cat_stats['processed'] += token_stat.processed_tokens
                
        # Calculate average reduction
        if stats['token_metrics']['total_original'] > 0:
            stats['token_metrics']['average_reduction'] = (
                (stats['token_metrics']['total_original'] - stats['token_metrics']['total_processed']) /
                stats['token_metrics']['total_original']
            ) * 100
            
        # Calculate category-specific reductions
        for cat, cat_stats in stats['token_metrics']['by_category'].items():
            if cat_stats['original'] > 0:
                cat_stats['reduction'] = (
                    (cat_stats['original'] - cat_stats['processed']) /
                    cat_stats['original']
                ) * 100
        
        # Analyze relationships
        relationship_counts = defaultdict(int)
        concept_connections = defaultdict(int)
        
        for rel in self.all_relationships:
            if isinstance(rel, dict):
                rel_type = rel.get('type', 'unknown')
                stats['relationship_metrics']['relationship_types'][rel_type] += 1
                
                source = rel.get('source', '')
                target = rel.get('target', '')
                if source:
                    concept_connections[source] += 1
                if target:
                    concept_connections[target] += 1
        
        # Get most connected concepts
        most_connected = sorted(
            concept_connections.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10 most connected
        
        stats['relationship_metrics']['most_connected_concepts'] = [
            {'concept': concept, 'connections': count}
            for concept, count in most_connected
        ]
        
        # Calculate average content length
        if stats['file_counts']['total'] > 0:
            stats['content_metrics']['average_content_length'] = (
                stats['token_metrics']['total_processed'] /
                stats['file_counts']['total']
            )
        
        return stats

def validate_yaml_file(file_path):
    """Validate a YAML file for syntax and structure.
    Returns (is_valid, error_message)"""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True, None
    except yaml.YAMLError as e:
        return False, f"YAML validation error in {file_path}: {str(e)}"
    except Exception as e:
        return False, f"Error reading {file_path}: {str(e)}"

def validate_kernel_schema(kernel_data):
    """Validate kernel YAML against expected schema.
    Returns (is_valid, error_message)"""
    schema = {
        "type": "object",
        "required": ["repo", "seed", "sigils", "identity", "actions"],
        "properties": {
            "repo": {"type": "string"},
            "seed": {"type": "string"},
            "sigils": {
                "type": "array",
                "items": {"type": "string"}
            },
            "identity": {"type": "string"},
            "actions": {"type": "string"},
            "prompt": {"type": "string"}
        }
    }
    
    try:
        jsonschema.validate(instance=kernel_data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, f"Kernel schema validation error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Process kernel files for Wonder.')
    parser.add_argument('kernel', help='Path to the kernel configuration file')
    parser.add_argument('--output', help='Path for the output file', required=True)
    args = parser.parse_args()
    
    # Get the base directory (where this script is located)
    base_dir = Path(__file__).parent.parent
    
    # Load configuration and schema
    config_path = base_dir / 'control' / 'gizzard-processing.yaml'
    schema_path = base_dir / 'control' / 'gizzard-schema.yaml'
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return
    
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        return
    
    try:
        processor = GizzardProcessor(str(config_path), str(schema_path))
    except jsonschema.exceptions.ValidationError:
        print("Configuration validation failed. Please check the configuration file.")
        return
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the WONDER_ROOT environment variable to point to your wonder project root.")
        return
    
    # Load preserve terms if available
    preserve_terms_path = base_dir / 'control' / 'preserve_terms.yaml'
    if preserve_terms_path.exists():
        processor.load_preserve_terms(str(preserve_terms_path))
    
    # Process the kernel
    processor.process_kernel(args.kernel, args.output)

if __name__ == '__main__':
    main() 