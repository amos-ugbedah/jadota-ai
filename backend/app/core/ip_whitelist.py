from typing import List, Optional
import ipaddress
from fastapi import Request, HTTPException, status

class IPWhitelist:
    """IP whitelist manager."""
    
    def __init__(self):
        self.whitelisted_ips: List[str] = []
        self.whitelisted_ranges: List[str] = []
    
    def add_ip(self, ip: str):
        """Add an IP to the whitelist."""
        self.whitelisted_ips.append(ip)
    
    def add_range(self, ip_range: str):
        """Add an IP range to the whitelist."""
        self.whitelisted_ranges.append(ip_range)
    
    def is_allowed(self, ip: str) -> bool:
        """Check if an IP is allowed."""
        # Check exact IP match
        if ip in self.whitelisted_ips:
            return True
        
        # Check IP range
        for ip_range in self.whitelisted_ranges:
            try:
                network = ipaddress.ip_network(ip_range)
                if ipaddress.ip_address(ip) in network:
                    return True
            except ValueError:
                continue
        
        return False
    
    def create_middleware(self, enabled: bool = False):
        """Create middleware for IP whitelisting."""
        async def ip_whitelist_middleware(request: Request, call_next):
            if not enabled:
                return await call_next(request)
            
            client_ip = request.client.host if request.client else None
            if not client_ip:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not found"
                )
            
            if not self.is_allowed(client_ip):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not whitelisted"
                )
            
            return await call_next(request)
        
        return ip_whitelist_middleware

# Global whitelist instance
whitelist = IPWhitelist()
