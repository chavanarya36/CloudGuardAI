"""Quick test of scanner on TerraGoat content"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.scanners.integrated_scanner import IntegratedSecurityScanner

# Sample TerraGoat content with known vulnerabilities
test_content = '''
resource "azurerm_sql_server" "example" {
  name                         = "terragoat-sqlserver-${var.environment}${random_integer.rnd_int.result}"
  resource_group_name          = azurerm_resource_group.example.name
  location                     = azurerm_resource_group.example.location
  version                      = "12.0"
  administrator_login          = "ariel"
  administrator_login_password = "Aa12345678"
}
'''

scanner = IntegratedSecurityScanner()
results = scanner.scan_file_integrated("test.tf", test_content)

print("\nTest Results:")
print(f"Total findings: {results.get('summary', {}).get('total_findings', 0)}")
print("\nFindings by scanner:")

# Check findings dict
findings_dict = results.get('findings', {})
for scanner_name, findings_list in findings_dict.items():
    print(f"  {scanner_name}: {len(findings_list)} findings")
    for finding in findings_list:
        print(f"    - {finding.get('title')}: {finding.get('description')}")

print("\nRisk Scores:")
scores = results.get('scores', {})
for score_name, score_value in scores.items():
    print(f"  {score_name}: {score_value}")
