"""
Task Logger for OllamaX-AI
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio

@dataclass
class LogEntry:
    timestamp: str
    level: str
    agent_id: str
    agent_type: str
    action: str
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    success: bool = True

class TaskLogger:
    """
    Comprehensive logging system for OllamaX-AI tasks and agent activities
    """
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup file logging
        self.setup_logging()
        
        # In-memory log storage for quick access
        self.recent_logs = []
        self.max_recent_logs = 1000
        
        # Performance metrics
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'agent_performance': {},
            'average_execution_time': 0.0
        }
    
    def setup_logging(self):
        """Setup file-based logging"""
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Main log file
        main_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'ollamax.log')
        )
        main_handler.setFormatter(formatter)
        
        # Error log file
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'errors.log')
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger('ollamax')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
    
    async def log_task_start(self, task_id: str, task_description: str, agent_type: str) -> None:
        """Log task start"""
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            agent_id=task_id,
            agent_type=agent_type,
            action="task_start",
            message=f"Starting task: {task_description}",
            data={"task_description": task_description}
        )
        
        await self._write_log(entry)
        self.metrics['total_tasks'] += 1
    
    async def log_task_complete(self, task_id: str, agent_type: str, success: bool, execution_time: float, result: Any = None) -> None:
        """Log task completion"""
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO" if success else "ERROR",
            agent_id=task_id,
            agent_type=agent_type,
            action="task_complete",
            message=f"Task {'completed successfully' if success else 'failed'}",
            data={"result": str(result)[:500] if result else None},
            execution_time=execution_time,
            success=success
        )
        
        await self._write_log(entry)
        
        # Update metrics
        if success:
            self.metrics['successful_tasks'] += 1
        else:
            self.metrics['failed_tasks'] += 1
        
        # Update agent performance
        if agent_type not in self.metrics['agent_performance']:
            self.metrics['agent_performance'][agent_type] = {
                'total_tasks': 0,
                'successful_tasks': 0,
                'average_execution_time': 0.0
            }
        
        agent_metrics = self.metrics['agent_performance'][agent_type]
        agent_metrics['total_tasks'] += 1
        
        if success:
            agent_metrics['successful_tasks'] += 1
        
        # Update average execution time
        current_avg = agent_metrics['average_execution_time']
        total_tasks = agent_metrics['total_tasks']
        agent_metrics['average_execution_time'] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
    
    async def log_agent_action(self, agent_id: str, agent_type: str, action: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log agent action"""
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            agent_id=agent_id,
            agent_type=agent_type,
            action=action,
            message=message,
            data=data
        )
        
        await self._write_log(entry)
    
    async def log_error(self, agent_id: str, agent_type: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error"""
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="ERROR",
            agent_id=agent_id,
            agent_type=agent_type,
            action="error",
            message=str(error),
            data={"error_type": type(error).__name__, "context": context},
            success=False
        )
        
        await self._write_log(entry)
        self.logger.error(f"Agent {agent_id} ({agent_type}): {error}", exc_info=True)
    
    async def log_security_event(self, agent_id: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log security-related events"""
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="WARNING",
            agent_id=agent_id,
            agent_type="security",
            action="security_event",
            message=f"Security event: {event_type}",
            data=details
        )
        
        await self._write_log(entry)
        
        # Also write to security log
        security_log_path = os.path.join(self.log_dir, 'security.log')
        with open(security_log_path, 'a') as f:
            f.write(f"{entry.timestamp} - {event_type}: {json.dumps(details)}\n")
    
    async def _write_log(self, entry: LogEntry) -> None:
        """Write log entry to storage"""
        
        # Add to recent logs
        self.recent_logs.append(entry)
        if len(self.recent_logs) > self.max_recent_logs:
            self.recent_logs.pop(0)
        
        # Write to file
        log_data = asdict(entry)
        
        # Daily log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        daily_log_path = os.path.join(self.log_dir, f'daily_{date_str}.jsonl')
        
        with open(daily_log_path, 'a') as f:
            f.write(json.dumps(log_data) + '\n')
        
        # Standard logging
        if entry.level == "ERROR":
            self.logger.error(f"{entry.agent_type}:{entry.action} - {entry.message}")
        elif entry.level == "WARNING":
            self.logger.warning(f"{entry.agent_type}:{entry.action} - {entry.message}")
        else:
            self.logger.info(f"{entry.agent_type}:{entry.action} - {entry.message}")
    
    def get_recent_logs(self, limit: int = 100, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        
        logs = self.recent_logs[-limit:]
        
        if agent_type:
            logs = [log for log in logs if log.agent_type == agent_type]
        
        return [asdict(log) for log in logs]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        
        total_tasks = self.metrics['total_tasks']
        success_rate = (
            self.metrics['successful_tasks'] / total_tasks 
            if total_tasks > 0 else 0.0
        )
        
        return {
            **self.metrics,
            'success_rate': success_rate,
            'failure_rate': 1.0 - success_rate
        }
    
    def get_agent_performance(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Get agent performance metrics"""
        
        if agent_type:
            return self.metrics['agent_performance'].get(agent_type, {})
        
        return self.metrics['agent_performance']
    
    async def export_logs(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Export logs to file"""
        
        export_path = os.path.join(self.log_dir, f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'metrics': self.get_metrics(),
            'agent_performance': self.get_agent_performance(),
            'recent_logs': self.get_recent_logs(1000)
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return export_path
    
    async def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up old log files"""
        
        import time
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for filename in os.listdir(self.log_dir):
            file_path = os.path.join(self.log_dir, filename)
            
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up old log file: {filename}")
                    except Exception as e:
                        self.logger.error(f"Failed to clean up {filename}: {e}")
    
    def search_logs(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs by query"""
        
        results = []
        query_lower = query.lower()
        
        for log in reversed(self.recent_logs):
            if (query_lower in log.message.lower() or 
                query_lower in log.action.lower() or
                query_lower in log.agent_type.lower()):
                
                results.append(asdict(log))
                
                if len(results) >= limit:
                    break
        
        return results