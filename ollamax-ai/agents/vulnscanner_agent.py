"""
Vulnerability Scanner Agent - Security scanning and vulnerability detection
"""

from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class VulnScannerAgent(BaseAgent):
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "vulnscanner")
        self.vulnerability_database = self._load_vulnerability_database()
    
    def _load_vulnerability_database(self) -> Dict[str, Any]:
        """Load vulnerability patterns and signatures"""
        return {
            "code_patterns": {
                "sql_injection": [
                    r"execute\s*\(\s*[\"'].*\+.*[\"']\s*\)",
                    r"query\s*\(\s*[\"'].*\%s.*[\"']\s*\)",
                    r"cursor\.execute\s*\(\s*[\"'].*\+.*[\"']\s*\)"
                ],
                "xss": [
                    r"innerHTML\s*=\s*.*\+",
                    r"document\.write\s*\(\s*.*\+",
                    r"eval\s*\(\s*.*user"
                ],
                "command_injection": [
                    r"os\.system\s*\(\s*.*\+",
                    r"subprocess\.\w+\s*\(\s*.*\+",
                    r"exec\s*\(\s*.*user"
                ],
                "path_traversal": [
                    r"open\s*\(\s*.*\+.*[\"']\.\./",
                    r"file\s*\(\s*.*user.*[\"']\.\./",
                    r"include\s*\(\s*.*\$_"
                ]
            },
            "dependency_vulnerabilities": {
                "python": ["requests<2.20.0", "flask<1.0", "django<2.2"],
                "javascript": ["lodash<4.17.12", "axios<0.18.1", "express<4.17.1"],
                "java": ["log4j<2.15.0", "spring<5.3.0", "jackson<2.10.0"]
            }
        }
    
    async def _execute_action(self, action: AgentAction) -> Any:
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "scan_code":
            return await self._scan_code(
                parameters.get('code', ''),
                parameters.get('language', 'python'),
                parameters.get('scan_type', 'comprehensive')
            )
        elif action_type == "scan_dependencies":
            return await self._scan_dependencies(
                parameters.get('dependencies', []),
                parameters.get('language', 'python')
            )
        elif action_type == "generate_report":
            return await self._generate_security_report(parameters.get('findings', []))
        else:
            return {"error": f"Unknown vulnerability scanner action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        return [
            "code_scanner",
            "dependency_checker",
            "vulnerability_detector",
            "security_reporter",
            "cve_lookup",
            "pattern_matcher"
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a vulnerability scanner agent specialized in detecting security issues in code and dependencies.

Your capabilities include:
- Static code analysis for security vulnerabilities
- Dependency vulnerability scanning
- Security pattern detection
- CVE database lookup
- Security report generation

Focus on identifying:
- Injection vulnerabilities (SQL, XSS, Command)
- Authentication and authorization flaws
- Sensitive data exposure
- Security misconfigurations
- Vulnerable dependencies
- Cryptographic issues

Always provide:
- Clear vulnerability descriptions
- Risk assessments
- Remediation guidance
- Best practice recommendations"""
    
    async def _scan_code(self, code: str, language: str, scan_type: str) -> Dict[str, Any]:
        """Scan code for security vulnerabilities"""
        
        # Use security-focused model
        routing_decision = self.model_router.route_task(
            f"security scan {language} code",
            context={'agent_type': 'vulnscanner', 'task_type': 'vulnerability_scan'}
        )
        
        # Pattern-based scanning
        pattern_findings = self._scan_with_patterns(code, language)
        
        # AI-based analysis
        scan_prompt = f"""
Perform a comprehensive security scan of the following {language} code:

```{language}
{code}
```

Scan Type: {scan_type}

Analyze for:

1. INJECTION VULNERABILITIES:
   - SQL injection
   - XSS (Cross-site scripting)
   - Command injection
   - LDAP injection
   - XML injection

2. AUTHENTICATION/AUTHORIZATION:
   - Weak authentication
   - Missing authorization checks
   - Session management issues
   - Privilege escalation

3. DATA EXPOSURE:
   - Sensitive data in logs
   - Hardcoded credentials
   - Information disclosure
   - Insecure data storage

4. CRYPTOGRAPHIC ISSUES:
   - Weak encryption
   - Insecure random numbers
   - Poor key management
   - Hash vulnerabilities

5. CONFIGURATION ISSUES:
   - Debug mode enabled
   - Default credentials
   - Insecure defaults
   - Missing security headers

Provide detailed findings with:
- Vulnerability type and severity
- Affected code location
- Exploitation scenario
- Remediation steps

Security Scan Results:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=scan_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            ai_analysis = response.response
            
            # Combine pattern and AI findings
            all_findings = pattern_findings + self._parse_ai_findings(ai_analysis)
            
            return {
                "success": True,
                "code": code,
                "language": language,
                "scan_type": scan_type,
                "findings": all_findings,
                "ai_analysis": ai_analysis,
                "risk_score": self._calculate_risk_score(all_findings),
                "summary": self._generate_findings_summary(all_findings)
            }
            
        except Exception as e:
            return {"error": f"Code scanning failed: {e}"}
    
    async def _scan_dependencies(self, dependencies: List[str], language: str) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities"""
        
        vulnerable_deps = []
        
        if language in self.vulnerability_database["dependency_vulnerabilities"]:
            known_vulns = self.vulnerability_database["dependency_vulnerabilities"][language]
            
            for dep in dependencies:
                for vuln_pattern in known_vulns:
                    if self._matches_vulnerability_pattern(dep, vuln_pattern):
                        vulnerable_deps.append({
                            "dependency": dep,
                            "vulnerability": vuln_pattern,
                            "severity": "high",
                            "description": f"Known vulnerability in {dep}"
                        })
        
        return {
            "success": True,
            "dependencies_scanned": len(dependencies),
            "vulnerabilities_found": len(vulnerable_deps),
            "vulnerable_dependencies": vulnerable_deps,
            "language": language
        }
    
    async def _generate_security_report(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        routing_decision = self.model_router.route_task(
            "generate security vulnerability report",
            context={'agent_type': 'vulnscanner', 'task_type': 'documentation'}
        )
        
        report_prompt = f"""
Generate a comprehensive security vulnerability report based on these findings:

Findings:
{findings}

The report should include:

EXECUTIVE SUMMARY:
- Overall security posture
- Critical vulnerabilities summary
- Risk assessment
- Immediate actions required

VULNERABILITY DETAILS:
For each finding:
- Vulnerability ID and type
- Severity rating (Critical/High/Medium/Low)
- Affected components
- Technical description
- Proof of concept (if applicable)
- Business impact
- CVSS score (if applicable)

RISK ASSESSMENT:
- Risk matrix
- Threat modeling
- Attack scenarios
- Potential impact

REMEDIATION PLAN:
- Immediate fixes (0-7 days)
- Short-term improvements (1-4 weeks)
- Long-term security enhancements (1-6 months)
- Security best practices

APPENDICES:
- Technical details
- References and resources
- Compliance mapping

Security Report:"""
        
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
            
            return {
                "success": True,
                "report_content": report_content,
                "findings_count": len(findings),
                "critical_count": len([f for f in findings if f.get("severity") == "critical"]),
                "high_count": len([f for f in findings if f.get("severity") == "high"]),
                "generated_at": "current_timestamp"
            }
            
        except Exception as e:
            return {"error": f"Report generation failed: {e}"}
    
    def _scan_with_patterns(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Scan code using predefined vulnerability patterns"""
        
        findings = []
        
        if language not in self.vulnerability_database["code_patterns"]:
            return findings
        
        patterns = self.vulnerability_database["code_patterns"]
        
        for vuln_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                import re
                matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    findings.append({
                        "type": vuln_type,
                        "severity": self._get_pattern_severity(vuln_type),
                        "location": {
                            "start": match.start(),
                            "end": match.end(),
                            "line": code[:match.start()].count('\n') + 1
                        },
                        "matched_code": match.group(0),
                        "description": f"Potential {vuln_type} vulnerability detected",
                        "source": "pattern_matching"
                    })
        
        return findings
    
    def _parse_ai_findings(self, ai_analysis: str) -> List[Dict[str, Any]]:
        """Parse AI analysis into structured findings"""
        
        findings = []
        lines = ai_analysis.split('\n')
        
        current_finding = None
        for line in lines:
            line = line.strip()
            
            # Look for vulnerability indicators
            if any(keyword in line.lower() for keyword in ['vulnerability', 'security issue', 'risk']):
                if current_finding:
                    findings.append(current_finding)
                
                current_finding = {
                    "type": "ai_detected",
                    "severity": "medium",
                    "description": line,
                    "source": "ai_analysis"
                }
            elif current_finding and line.startswith('-'):
                if "severity" in line.lower():
                    severity_match = re.search(r'(critical|high|medium|low)', line.lower())
                    if severity_match:
                        current_finding["severity"] = severity_match.group(1)
        
        if current_finding:
            findings.append(current_finding)
        
        return findings
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score based on findings"""
        
        if not findings:
            return 0.0
        
        severity_weights = {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 1.0
        }
        
        total_score = 0.0
        for finding in findings:
            severity = finding.get("severity", "low")
            total_score += severity_weights.get(severity, 1.0)
        
        # Normalize to 0-100 scale
        max_possible = len(findings) * 10.0
        return min(100.0, (total_score / max_possible) * 100.0)
    
    def _generate_findings_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of findings"""
        
        summary = {
            "total_findings": len(findings),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "by_type": {}
        }
        
        for finding in findings:
            severity = finding.get("severity", "low")
            vuln_type = finding.get("type", "unknown")
            
            summary[severity] += 1
            
            if vuln_type not in summary["by_type"]:
                summary["by_type"][vuln_type] = 0
            summary["by_type"][vuln_type] += 1
        
        return summary
    
    def _get_pattern_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type"""
        
        severity_map = {
            "sql_injection": "high",
            "xss": "medium",
            "command_injection": "critical",
            "path_traversal": "high"
        }
        
        return severity_map.get(vuln_type, "medium")
    
    def _matches_vulnerability_pattern(self, dependency: str, pattern: str) -> bool:
        """Check if dependency matches vulnerability pattern"""
        
        # Simple version comparison (in production would use proper semver)
        if "<" in pattern:
            dep_name, version_constraint = pattern.split("<")
            return dep_name.strip() in dependency
        
        return False