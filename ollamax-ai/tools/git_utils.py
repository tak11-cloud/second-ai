"""
Git utilities for OllamaX-AI
"""

import os
import subprocess
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class GitUtils:
    """
    Git utilities for version control operations
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        
    def is_git_repo(self) -> bool:
        """Check if directory is a git repository"""
        
        git_dir = os.path.join(self.repo_path, '.git')
        return os.path.exists(git_dir)
    
    def init_repo(self) -> Dict[str, Any]:
        """Initialize git repository"""
        
        try:
            result = subprocess.run(
                ['git', 'init'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get git status"""
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                files = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        status = line[:2]
                        filename = line[3:]
                        files.append({
                            'status': status,
                            'filename': filename,
                            'staged': status[0] != ' ',
                            'modified': status[1] != ' '
                        })
                
                return {
                    'success': True,
                    'files': files,
                    'clean': len(files) == 0
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_files(self, files: List[str]) -> Dict[str, Any]:
        """Add files to staging area"""
        
        try:
            cmd = ['git', 'add'] + files
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def commit(self, message: str, author: Optional[str] = None) -> Dict[str, Any]:
        """Commit changes"""
        
        try:
            cmd = ['git', 'commit', '-m', message]
            
            if author:
                cmd.extend(['--author', author])
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_diff(self, staged: bool = False) -> Dict[str, Any]:
        """Get diff of changes"""
        
        try:
            cmd = ['git', 'diff']
            if staged:
                cmd.append('--staged')
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'diff': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_log(self, limit: int = 10) -> Dict[str, Any]:
        """Get commit log"""
        
        try:
            result = subprocess.run(
                ['git', 'log', f'--max-count={limit}', '--oneline'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1] if len(parts) > 1 else ''
                        })
                
                return {
                    'success': True,
                    'commits': commits
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create new branch"""
        
        try:
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """Switch to branch"""
        
        try:
            result = subprocess.run(
                ['git', 'checkout', branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_current_branch(self) -> Dict[str, Any]:
        """Get current branch name"""
        
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'branch': result.stdout.strip(),
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_branches(self) -> Dict[str, Any]:
        """Get list of branches"""
        
        try:
            result = subprocess.run(
                ['git', 'branch'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                branches = []
                current_branch = None
                
                for line in result.stdout.strip().split('\n'):
                    if line:
                        if line.startswith('*'):
                            current_branch = line[2:].strip()
                            branches.append(current_branch)
                        else:
                            branches.append(line.strip())
                
                return {
                    'success': True,
                    'branches': branches,
                    'current_branch': current_branch
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stash_changes(self, message: Optional[str] = None) -> Dict[str, Any]:
        """Stash current changes"""
        
        try:
            cmd = ['git', 'stash']
            if message:
                cmd.extend(['push', '-m', message])
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def apply_stash(self, stash_index: int = 0) -> Dict[str, Any]:
        """Apply stashed changes"""
        
        try:
            result = subprocess.run(
                ['git', 'stash', 'apply', f'stash@{{{stash_index}}}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_file_history(self, filename: str, limit: int = 10) -> Dict[str, Any]:
        """Get commit history for specific file"""
        
        try:
            result = subprocess.run(
                ['git', 'log', f'--max-count={limit}', '--oneline', '--', filename],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1] if len(parts) > 1 else ''
                        })
                
                return {
                    'success': True,
                    'commits': commits,
                    'filename': filename
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reset_file(self, filename: str) -> Dict[str, Any]:
        """Reset file to last committed state"""
        
        try:
            result = subprocess.run(
                ['git', 'checkout', 'HEAD', '--', filename],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_remote_info(self) -> Dict[str, Any]:
        """Get remote repository information"""
        
        try:
            result = subprocess.run(
                ['git', 'remote', '-v'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                remotes = {}
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 3:
                            name = parts[0]
                            url = parts[1]
                            operation = parts[2].strip('()')
                            
                            if name not in remotes:
                                remotes[name] = {}
                            remotes[name][operation] = url
                
                return {
                    'success': True,
                    'remotes': remotes
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}