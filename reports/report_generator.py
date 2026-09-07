import os
import csv
from datetime import datetime
from activity_log.activity_logger import get_sent_logs, SENT_LOG_CSV

def get_campaign_statistics():
    """
    Computes summary metrics from all sent log entries:
    - Total attempts
    - Successful sends (sent/simulated)
    - Failed sends
    - Success rate
    """
    logs = get_sent_logs()
    
    total = len(logs)
    success = 0
    failed = 0
    
    for entry in logs:
        status = entry.get('status', '').lower()
        if status in ['sent', 'simulated']:
            success += 1
        elif status == 'failed':
            failed += 1
            
    success_rate = (success / total * 100) if total > 0 else 0.0
    
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success_rate, 2),
        "recent_sends": logs[-100:]  # Return up to last 100 send attempts
    }

def get_last_run_statistics():
    """
    Reads the last consecutive sequence of sends from the log file 
    to represent the 'most recent campaign run' metrics.
    """
    logs = get_sent_logs()
    if not logs:
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "success_rate": 0,
            "recipients": []
        }
        
    # We find the boundary of the last run by looking for a sequence of 
    # attempts close to each other in time, or simply the last campaign batch
    # Let's group entries by campaign name (e.g. "Singing Bowls Outreach") 
    # and retrieve the latest contiguous block of sends.
    last_campaign = logs[-1].get('campaign_name', 'Singing Bowls Outreach')
    
    # Trace backwards to capture the last contiguous block of sends for this campaign
    last_run_logs = []
    for entry in reversed(logs):
        if entry.get('campaign_name') == last_campaign:
            last_run_logs.append(entry)
        else:
            break
            
    last_run_logs.reverse()
    
    total = len(last_run_logs)
    success = sum(1 for e in last_run_logs if e.get('status') in ['sent', 'simulated'])
    failed = sum(1 for e in last_run_logs if e.get('status') == 'failed')
    success_rate = (success / total * 100) if total > 0 else 0.0
    
    return {
        "campaign_name": last_campaign,
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success_rate, 2),
        "recipients": last_run_logs
    }
