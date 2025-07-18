#!/usr/bin/env python3
"""
Connection diagnostics module for BlueFusion UI
Provides detailed error information and troubleshooting
"""
import httpx
import asyncio
import websockets
import socket
from typing import Dict, Any, Tuple

class ConnectionDiagnostics:
    """Diagnose connection issues between Gradio and FastAPI"""
    
    @staticmethod
    def check_port_open(host: str, port: int) -> bool:
        """Check if a port is open and listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def diagnose_api_connection(base_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
        """Comprehensive API connection diagnosis"""
        results = {
            "api_reachable": False,
            "cors_headers_present": False,
            "error_details": None,
            "suggestions": []
        }
        
        # Extract host and port
        import urllib.parse
        parsed = urllib.parse.urlparse(base_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8000
        
        # Check if port is open
        if not ConnectionDiagnostics.check_port_open(host, port):
            results["error_details"] = f"Port {port} is not open on {host}"
            results["suggestions"].extend([
                "Ensure the FastAPI server is running",
                f"Run: cd src/api && python fastapi_server.py",
                "Check if another process is using port 8000"
            ])
            return results
        
        # Try to connect to API
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{base_url}/")
                results["api_reachable"] = True
                
                # Check CORS headers
                cors_headers = {k: v for k, v in response.headers.items() 
                               if "access-control" in k.lower()}
                results["cors_headers_present"] = len(cors_headers) > 0
                results["cors_headers"] = cors_headers
                
                if not results["cors_headers_present"]:
                    results["suggestions"].append("CORS headers missing - check FastAPI middleware configuration")
                    
        except httpx.ConnectError as e:
            results["error_details"] = f"Connection error: {str(e)}"
            results["suggestions"].extend([
                "Check firewall settings",
                "Try using 127.0.0.1 instead of localhost",
                "Verify no proxy is interfering"
            ])
        except httpx.TimeoutException:
            results["error_details"] = "Connection timeout"
            results["suggestions"].extend([
                "API server may be overloaded",
                "Check system resources",
                "Increase timeout settings"
            ])
        except Exception as e:
            results["error_details"] = f"Unexpected error: {str(e)}"
            results["suggestions"].append("Check API server logs for errors")
        
        return results
    
    @staticmethod
    async def diagnose_websocket_connection(ws_url: str = "ws://127.0.0.1:8000/stream") -> Dict[str, Any]:
        """Diagnose WebSocket connection"""
        results = {
            "ws_connectable": False,
            "error_details": None,
            "suggestions": []
        }
        
        try:
            async with websockets.connect(ws_url, close_timeout=2) as websocket:
                results["ws_connectable"] = True
                # Try to send a ping
                await websocket.ping()
        except websockets.exceptions.WebSocketException as e:
            results["error_details"] = f"WebSocket error: {str(e)}"
            results["suggestions"].extend([
                "Check if WebSocket endpoint exists in FastAPI",
                "Verify WebSocket URL is correct",
                "Check for proxy/firewall blocking WebSocket connections"
            ])
        except Exception as e:
            results["error_details"] = f"Connection error: {str(e)}"
            results["suggestions"].append("Ensure API server supports WebSocket connections")
        
        return results
    
    @staticmethod
    def get_diagnostic_report(api_url: str = "http://127.0.0.1:8000", 
                            ws_url: str = "ws://127.0.0.1:8000/stream") -> str:
        """Generate a comprehensive diagnostic report"""
        report = ["=== BlueFusion Connection Diagnostics ===\n"]
        
        # API Diagnostics
        report.append("## API Connection Test")
        api_results = ConnectionDiagnostics.diagnose_api_connection(api_url)
        
        if api_results["api_reachable"]:
            report.append("✅ API is reachable")
            if api_results["cors_headers_present"]:
                report.append("✅ CORS headers are present")
                for header, value in api_results.get("cors_headers", {}).items():
                    report.append(f"   {header}: {value}")
            else:
                report.append("❌ CORS headers missing")
        else:
            report.append("❌ API is not reachable")
            report.append(f"   Error: {api_results['error_details']}")
        
        if api_results["suggestions"]:
            report.append("\n### Suggestions:")
            for suggestion in api_results["suggestions"]:
                report.append(f"• {suggestion}")
        
        # WebSocket Diagnostics
        report.append("\n## WebSocket Connection Test")
        ws_results = asyncio.run(ConnectionDiagnostics.diagnose_websocket_connection(ws_url))
        
        if ws_results["ws_connectable"]:
            report.append("✅ WebSocket connection successful")
        else:
            report.append("❌ WebSocket connection failed")
            report.append(f"   Error: {ws_results['error_details']}")
        
        if ws_results["suggestions"]:
            report.append("\n### Suggestions:")
            for suggestion in ws_results["suggestions"]:
                report.append(f"• {suggestion}")
        
        # System Information
        report.append("\n## System Information")
        report.append(f"• Python version: {sys.version.split()[0]}")
        try:
            import gradio
            report.append(f"• Gradio version: {gradio.__version__}")
        except:
            report.append("• Gradio: Not installed")
        try:
            import fastapi
            report.append(f"• FastAPI version: {fastapi.__version__}")
        except:
            report.append("• FastAPI: Not installed")
        
        # Common Issues
        report.append("\n## Common Issues and Solutions")
        report.append("1. **CORS Errors in Browser Console**")
        report.append("   - Update CORS origins in fastapi_server.py")
        report.append("   - Clear browser cache and cookies")
        report.append("   - Try incognito/private browsing mode")
        report.append("\n2. **Connection Refused Errors**")
        report.append("   - Ensure FastAPI server is running")
        report.append("   - Check if ports 8000 (API) and 7860 (Gradio) are free")
        report.append("   - Disable firewall temporarily for testing")
        report.append("\n3. **WebSocket Connection Failed**")
        report.append("   - Check browser console for specific WebSocket errors")
        report.append("   - Ensure no proxy is blocking WebSocket upgrade")
        report.append("   - Try different browser")
        
        return "\n".join(report)


# Enhanced error handler for Gradio
def handle_api_error(func):
    """Decorator to handle API errors with detailed diagnostics"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Generate diagnostic report
            diagnostics = ConnectionDiagnostics()
            report = diagnostics.get_diagnostic_report()
            
            error_message = f"""
## ❌ API Connection Error

**Error:** {str(e)}

### Diagnostic Report:
{report}

### Quick Actions:
1. Check if API server is running: `ps aux | grep fastapi`
2. Restart API server: `cd src/api && python fastapi_server.py`
3. Check browser console: Press F12 and look for errors
"""
            return error_message
    return wrapper


if __name__ == "__main__":
    import sys
    diagnostics = ConnectionDiagnostics()
    print(diagnostics.get_diagnostic_report())