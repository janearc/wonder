from typing import List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import git

class GitCommitEntry(BaseModel):
    commit_hash: str = Field(..., description="The commit hash")
    date: datetime = Field(..., description="The datetime of the commit")
    additions: int = Field(..., description="Number of additions in this commit")
    deletions: int = Field(..., description="Number of deletions in this commit")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

class GitStats(BaseModel):
    last_modified_commit: str = Field(..., description="Hash of the last modifying commit")
    commit_count: int = Field(..., description="Number of commits affecting this file")
    commit_history: List[GitCommitEntry] = Field(..., description="Chronological commit history for the file")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    def total_additions(self) -> int:
        return sum(commit.additions for commit in self.commit_history)

    def total_deletions(self) -> int:
        return sum(commit.deletions for commit in self.commit_history)

    def total_commits(self) -> int:
        return len(self.commit_history)

def get_git_stats(filepath: str) -> GitStats:
    repo = git.Repo(path=filepath, search_parent_directories=True)
    rel_path = str(filepath).replace(str(repo.working_tree_dir) + "/", "")

    commits = list(repo.iter_commits(paths=rel_path))
    commit_history = []

    for commit in reversed(commits):
        stats = commit.stats.files.get(rel_path, {"insertions": 0, "deletions": 0})
        commit_history.append(GitCommitEntry(
            commit_hash=commit.hexsha,
            date=commit.committed_datetime,
            additions=stats.get("insertions", 0),
            deletions=stats.get("deletions", 0),
        ))

    return GitStats(
        last_modified_commit=commits[0].hexsha if commits else "",
        commit_count=len(commits),
        commit_history=commit_history
    )

