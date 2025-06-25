# api/routes/security_admin.py

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from api.security.ip_security import security_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/security", tags=["Security Administration"])

# Pydantic models for request/response
class IPWhitelistRequest(BaseModel):
    ip: str
    reason: Optional[str] = None

class IPUnblockRequest(BaseModel):
    ip: str

class SecurityConfigUpdate(BaseModel):
    max_requests_per_window: Optional[int] = None
    rate_limit_window: Optional[int] = None
    max_404_errors: Optional[int] = None
    block_duration: Optional[int] = None
    max_errors_per_window: Optional[int] = None

def verify_admin_access(request: Request):
    """Simple admin verification - you should enhance this with proper authentication"""
    client_ip = security_manager.get_client_ip(request)
    
    # For now, only allow localhost access to admin endpoints
    # In production, you should implement proper authentication
    if client_ip not in ["127.0.0.1", "::1", "localhost"]:
        raise HTTPException(status_code=403, detail="Admin access restricted to localhost")
    
    return True

@router.get("/stats")
async def get_security_stats(request: Request, _: bool = Depends(verify_admin_access)):
    """Get comprehensive security statistics"""
    try:
        stats = security_manager.get_security_stats()
        blocked_ips = security_manager.get_blocked_ips()
        
        return {
            "status": "success",
            "statistics": stats,
            "blocked_ips": blocked_ips,
            "blocked_count": len(blocked_ips),
            "system_health": "operational"
        }
    except Exception as e:
        logger.error(f"Error getting security stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security statistics")

@router.get("/blocked-ips")
async def get_blocked_ips(request: Request, _: bool = Depends(verify_admin_access)):
    """Get list of currently blocked IPs with details"""
    try:
        blocked_ips = security_manager.get_blocked_ips()
        
        return {
            "status": "success",
            "blocked_ips": blocked_ips,
            "total_blocked": len(blocked_ips),
            "message": f"Currently tracking {len(blocked_ips)} blocked IPs"
        }
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve blocked IPs")

@router.post("/whitelist/add")
async def add_to_whitelist(
    whitelist_request: IPWhitelistRequest, 
    request: Request,
    _: bool = Depends(verify_admin_access)
):
    """Add an IP to the whitelist"""
    try:
        ip = whitelist_request.ip.strip()
        
        # Basic IP validation
        if not ip or ip == "unknown":
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        # Add to whitelist
        security_manager.add_to_whitelist(ip)
        
        # Also unblock if currently blocked
        was_blocked = security_manager.unblock_ip(ip)
        
        logger.info(f"🔐 Admin added IP {ip} to whitelist from {security_manager.get_client_ip(request)}")
        
        return {
            "status": "success",
            "message": f"IP {ip} added to whitelist",
            "ip": ip,
            "was_blocked": was_blocked,
            "reason": whitelist_request.reason
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding IP to whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add IP to whitelist")

@router.delete("/whitelist/{ip}")
async def remove_from_whitelist(
    ip: str, 
    request: Request,
    _: bool = Depends(verify_admin_access)
):
    """Remove an IP from the whitelist"""
    try:
        ip = ip.strip()
        
        if not ip:
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        security_manager.remove_from_whitelist(ip)
        
        logger.info(f"🔐 Admin removed IP {ip} from whitelist from {security_manager.get_client_ip(request)}")
        
        return {
            "status": "success",
            "message": f"IP {ip} removed from whitelist",
            "ip": ip
        }
    except Exception as e:
        logger.error(f"Error removing IP from whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove IP from whitelist")

@router.post("/unblock")
async def unblock_ip(
    unblock_request: IPUnblockRequest,
    request: Request, 
    _: bool = Depends(verify_admin_access)
):
    """Manually unblock an IP address"""
    try:
        ip = unblock_request.ip.strip()
        
        if not ip:
            raise HTTPException(status_code=400, detail="Invalid IP address")
        
        success = security_manager.unblock_ip(ip)
        
        if success:
            logger.info(f"🔐 Admin unblocked IP {ip} from {security_manager.get_client_ip(request)}")
            return {
                "status": "success",
                "message": f"IP {ip} has been unblocked",
                "ip": ip
            }
        else:
            return {
                "status": "info",
                "message": f"IP {ip} was not currently blocked",
                "ip": ip
            }
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        raise HTTPException(status_code=500, detail="Failed to unblock IP")

@router.get("/whitelist")
async def get_whitelist(request: Request, _: bool = Depends(verify_admin_access)):
    """Get current whitelist"""
    try:
        whitelist = list(security_manager._whitelist)
        trusted_networks = list(security_manager._trusted_networks)
        
        return {
            "status": "success",
            "whitelist": whitelist,
            "trusted_networks": trusted_networks,
            "total_whitelisted": len(whitelist),
            "total_trusted_networks": len(trusted_networks)
        }
    except Exception as e:
        logger.error(f"Error getting whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve whitelist")

@router.put("/config")
async def update_security_config(
    config: SecurityConfigUpdate,
    request: Request,
    _: bool = Depends(verify_admin_access)
):
    """Update security configuration"""
    try:
        updated_fields = []
        
        if config.max_requests_per_window is not None:
            if config.max_requests_per_window < 1 or config.max_requests_per_window > 1000:
                raise HTTPException(status_code=400, detail="max_requests_per_window must be between 1 and 1000")
            security_manager.max_requests_per_window = config.max_requests_per_window
            updated_fields.append(f"max_requests_per_window: {config.max_requests_per_window}")
        
        if config.rate_limit_window is not None:
            if config.rate_limit_window < 10 or config.rate_limit_window > 3600:
                raise HTTPException(status_code=400, detail="rate_limit_window must be between 10 and 3600 seconds")
            security_manager.rate_limit_window = config.rate_limit_window
            updated_fields.append(f"rate_limit_window: {config.rate_limit_window}")
        
        if config.max_404_errors is not None:
            if config.max_404_errors < 1 or config.max_404_errors > 50:
                raise HTTPException(status_code=400, detail="max_404_errors must be between 1 and 50")
            security_manager.max_404_errors = config.max_404_errors
            updated_fields.append(f"max_404_errors: {config.max_404_errors}")
        
        if config.block_duration is not None:
            if config.block_duration < 60 or config.block_duration > 86400:
                raise HTTPException(status_code=400, detail="block_duration must be between 60 and 86400 seconds")
            security_manager.block_duration = config.block_duration
            updated_fields.append(f"block_duration: {config.block_duration}")
        
        if config.max_errors_per_window is not None:
            if config.max_errors_per_window < 1 or config.max_errors_per_window > 100:
                raise HTTPException(status_code=400, detail="max_errors_per_window must be between 1 and 100")
            security_manager.max_errors_per_window = config.max_errors_per_window
            updated_fields.append(f"max_errors_per_window: {config.max_errors_per_window}")
        
        if not updated_fields:
            raise HTTPException(status_code=400, detail="No valid configuration fields provided")
        
        logger.info(f"🔐 Admin updated security config from {security_manager.get_client_ip(request)}: {', '.join(updated_fields)}")
        
        return {
            "status": "success",
            "message": "Security configuration updated",
            "updated_fields": updated_fields,
            "current_config": security_manager.get_security_stats()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating security config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update security configuration")

@router.post("/cleanup")
async def trigger_cleanup(request: Request, _: bool = Depends(verify_admin_access)):
    """Manually trigger cleanup of expired security data"""
    try:
        security_manager.cleanup_expired_data()
        
        logger.info(f"🔐 Admin triggered security cleanup from {security_manager.get_client_ip(request)}")
        
        return {
            "status": "success",
            "message": "Security data cleanup completed",
            "timestamp": security_manager.stats.get("last_cleanup", "N/A")
        }
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup security data")

@router.get("/logs")
async def get_security_logs(
    request: Request,
    limit: int = 100,
    _: bool = Depends(verify_admin_access)
):
    """Get recent security events (basic implementation)"""
    try:
        # This is a basic implementation - in production you'd want proper log aggregation
        stats = security_manager.get_security_stats()
        blocked_ips = security_manager.get_blocked_ips()
        
        # Generate a simple security report
        events = []
        
        for ip, block_info in blocked_ips.items():
            events.append({
                "timestamp": block_info.get("blocked_at"),
                "type": "ip_blocked",
                "ip": ip,
                "reason": block_info.get("reason"),
                "duration": block_info.get("duration")
            })
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return {
            "status": "success",
            "events": events[:limit],
            "total_events": len(events),
            "stats_summary": {
                "total_requests": stats.get("total_requests", 0),
                "blocked_requests": stats.get("blocked_requests", 0),
                "ips_blocked": stats.get("ips_blocked", 0),
                "attacks_prevented": stats.get("attacks_prevented", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting security logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve security logs")

@router.get("/health")
async def security_health_check(request: Request):
    """Public security health check endpoint"""
    try:
        stats = security_manager.get_security_stats()
        
        return {
            "status": "operational",
            "security_system": "active",
            "currently_blocked_ips": stats.get("currently_blocked_ips", 0),
            "rate_limiting": "enabled",
            "auto_blocking": "enabled",
            "uptime_requests": stats.get("total_requests", 0)
        }
    except Exception as e:
        logger.error(f"Error in security health check: {e}")
        return {
            "status": "degraded",
            "error": "Security system health check failed"
        }
