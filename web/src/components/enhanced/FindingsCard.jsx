import React, { useState } from 'react';
import { AlertCircle, Info, XCircle, AlertTriangle, Shield, Key, Bug, CheckCircle, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

export default function FindingsCard({ findings, scannerBreakdown, complianceScore }) {
  const [expandedFindings, setExpandedFindings] = useState({});
  const [selectedFilter, setSelectedFilter] = useState('all');

  const toggleFinding = (index) => {
    setExpandedFindings(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getScannerConfig = (category) => {
    const configs = {
      secrets: {
        icon: Key,
        label: 'Secrets',
        color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
        borderColor: 'border-purple-500'
      },
      cve: {
        icon: Bug,
        label: 'CVE',
        color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
        borderColor: 'border-red-500'
      },
      compliance: {
        icon: Shield,
        label: 'Compliance',
        color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
        borderColor: 'border-blue-500'
      },
      rules: {
        icon: AlertCircle,
        label: 'Rules',
        color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
        borderColor: 'border-orange-500'
      }
    };
    return configs[category] || configs.rules;
  };

  const getSeverityConfig = (severity) => {
    const configs = {
      CRITICAL: {
        icon: XCircle,
        variant: 'destructive',
        bgClass: 'bg-red-50 dark:bg-red-950/20',
        borderClass: 'border-red-200 dark:border-red-900',
        iconColor: 'text-red-600 dark:text-red-400'
      },
      HIGH: {
        icon: AlertCircle,
        variant: 'destructive',
        bgClass: 'bg-orange-50 dark:bg-orange-950/20',
        borderClass: 'border-orange-200 dark:border-orange-900',
        iconColor: 'text-orange-600 dark:text-orange-400'
      },
      MEDIUM: {
        icon: AlertTriangle,
        variant: 'secondary',
        bgClass: 'bg-yellow-50 dark:bg-yellow-950/20',
        borderClass: 'border-yellow-200 dark:border-yellow-900',
        iconColor: 'text-yellow-600 dark:text-yellow-400'
      },
      LOW: {
        icon: Info,
        variant: 'outline',
        bgClass: 'bg-blue-50 dark:bg-blue-950/20',
        borderClass: 'border-blue-200 dark:border-blue-900',
        iconColor: 'text-blue-600 dark:text-blue-400'
      }
    };
    return configs[severity] || configs.LOW;
  };

  // Filter findings based on selected category
  const filteredFindings = selectedFilter === 'all' 
    ? findings 
    : findings.filter(f => f.category === selectedFilter);

  if (!findings || findings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Security Findings</CardTitle>
          <CardDescription>No security issues detected</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="rounded-full bg-green-100 dark:bg-green-950/20 p-4 mb-4">
              <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400" />
            </div>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              All Clear!
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              No security vulnerabilities found in your configuration
            </p>
            {complianceScore && (
              <div className="mt-4 px-4 py-2 bg-green-50 dark:bg-green-950/20 rounded-lg">
                <p className="text-sm font-medium text-green-700 dark:text-green-300">
                  Compliance Score: {complianceScore.toFixed(1)}/100
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Security Findings</CardTitle>
            <CardDescription>
              {filteredFindings.length} issue{filteredFindings.length !== 1 ? 's' : ''} detected
            </CardDescription>
          </div>
          {complianceScore !== undefined && complianceScore !== null && (
            <div className="text-right">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Compliance Score</div>
              <div className={`text-2xl font-bold ${complianceScore >= 90 ? 'text-green-600' : complianceScore >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                {typeof complianceScore === 'number' ? complianceScore.toFixed(0) : '0'}%
              </div>
            </div>
          )}
        </div>

        {/* Scanner Filter Buttons */}
        {scannerBreakdown && (
          <div className="flex flex-wrap gap-2 mt-4">
            <button
              onClick={() => setSelectedFilter('all')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                selectedFilter === 'all'
                  ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              All ({scannerBreakdown.total || findings.length})
            </button>
            {scannerBreakdown.secrets > 0 && (
              <button
                onClick={() => setSelectedFilter('secrets')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${
                  selectedFilter === 'secrets'
                    ? 'bg-purple-600 text-white'
                    : 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 hover:bg-purple-200'
                }`}
              >
                <Key className="w-3 h-3" />
                Secrets ({scannerBreakdown.secrets})
              </button>
            )}
            {scannerBreakdown.cve > 0 && (
              <button
                onClick={() => setSelectedFilter('cve')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${
                  selectedFilter === 'cve'
                    ? 'bg-red-600 text-white'
                    : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 hover:bg-red-200'
                }`}
              >
                <Bug className="w-3 h-3" />
                CVE ({scannerBreakdown.cve})
              </button>
            )}
            {scannerBreakdown.compliance > 0 && (
              <button
                onClick={() => setSelectedFilter('compliance')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${
                  selectedFilter === 'compliance'
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 hover:bg-blue-200'
                }`}
              >
                <Shield className="w-3 h-3" />
                Compliance ({scannerBreakdown.compliance})
              </button>
            )}
            {scannerBreakdown.rules > 0 && (
              <button
                onClick={() => setSelectedFilter('rules')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${
                  selectedFilter === 'rules'
                    ? 'bg-orange-600 text-white'
                    : 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300 hover:bg-orange-200'
                }`}
              >
                <AlertCircle className="w-3 h-3" />
                Rules ({scannerBreakdown.rules})
              </button>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {filteredFindings.map((finding, index) => {
          const config = getSeverityConfig(finding.severity);
          const scannerConfig = getScannerConfig(finding.category);
          const Icon = config.icon;
          const ScannerIcon = scannerConfig.icon;
          const isExpanded = expandedFindings[index];

          return (
            <div
              key={index}
              className={`p-4 rounded-lg border-l-4 ${config.borderClass} ${config.bgClass} transition-all hover:shadow-md`}
            >
              <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${config.iconColor}`} />
                <div className="flex-1 space-y-2">
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                      {finding.title || finding.check_id}
                    </h4>
                    <div className="flex items-center gap-2 shrink-0">
                      {finding.category && (
                        <Badge className={`${scannerConfig.color} text-xs flex items-center gap-1`}>
                          <ScannerIcon className="w-3 h-3" />
                          {scannerConfig.label}
                        </Badge>
                      )}
                      <Badge variant={config.variant} className="shrink-0">
                        {finding.severity}
                      </Badge>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {finding.description}
                  </p>

                  {/* CVE-specific information */}
                  {finding.cve_id && (
                    <div className="flex items-center gap-2 text-xs">
                      <a
                        href={`https://nvd.nist.gov/vuln/detail/${finding.cve_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                      >
                        <Bug className="w-3 h-3" />
                        {finding.cve_id}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                      {finding.cvss_score && (
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded font-medium">
                          CVSS: {finding.cvss_score}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Compliance-specific information */}
                  {finding.control_id && (
                    <div className="flex items-center gap-2 text-xs">
                      <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                        {finding.control_id}
                      </Badge>
                      {finding.compliance_framework && (
                        <span className="text-gray-600 dark:text-gray-400">
                          {finding.compliance_framework}
                        </span>
                      )}
                    </div>
                  )}
                  
                  {finding.resource && (
                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                      <span className="font-medium">Resource:</span>
                      <code className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                        {finding.resource}
                      </code>
                    </div>
                  )}
                  
                  {finding.file_path && (
                    <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                      <span className="font-medium">Location:</span>
                      <span>{finding.file_path}</span>
                      {finding.line_number && (
                        <span className="text-gray-500">Line {finding.line_number}</span>
                      )}
                    </div>
                  )}

                  {/* Collapsible Remediation Steps */}
                  {(finding.remediation_steps || finding.recommendation || finding.remediation) && (
                    <div className="mt-3">
                      <button
                        onClick={() => toggleFinding(index)}
                        className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                        💡 Remediation Steps
                      </button>
                      
                      {isExpanded && (
                        <div className="mt-2 p-3 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                          {finding.remediation_steps ? (
                            <ol className="list-decimal list-inside space-y-1 text-xs text-gray-600 dark:text-gray-400">
                              {finding.remediation_steps.map((step, idx) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ol>
                          ) : (
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {finding.recommendation || finding.remediation}
                            </p>
                          )}

                          {/* External references */}
                          {finding.references && finding.references.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                                📚 References
                              </p>
                              <ul className="space-y-1">
                                {finding.references.map((ref, idx) => (
                                  <li key={idx}>
                                    <a
                                      href={ref}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                                    >
                                      {ref.includes('nvd.nist.gov') ? 'NVD' : 
                                       ref.includes('cwe.mitre.org') ? 'CWE' :
                                       ref.includes('owasp.org') ? 'OWASP' :
                                       ref.includes('aws.amazon.com') ? 'AWS Docs' : 
                                       'Documentation'}
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
