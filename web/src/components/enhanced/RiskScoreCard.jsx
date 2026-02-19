import React from 'react';
import { Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';

export default function RiskScoreCard({ score, componentScores }) {
  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'Critical', color: 'from-red-500 to-orange-500', textColor: 'text-red-600', icon: AlertTriangle };
    if (score >= 60) return { level: 'High', color: 'from-orange-500 to-yellow-500', textColor: 'text-orange-600', icon: AlertTriangle };
    if (score >= 40) return { level: 'Medium', color: 'from-yellow-500 to-green-500', textColor: 'text-yellow-600', icon: Shield };
    return { level: 'Low', color: 'from-green-500 to-emerald-500', textColor: 'text-green-600', icon: CheckCircle2 };
  };

  const risk = getRiskLevel(score);
  const Icon = risk.icon;

  return (
    <Card className="overflow-hidden">
      <div className={`h-2 bg-linear-to-r ${risk.color}`}></div>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Risk Assessment</span>
          <Icon className={`w-6 h-6 ${risk.textColor}`} />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Risk Score */}
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full bg-linear-to-br ${risk.color} shadow-lg`}>
            <div className="flex flex-col items-center bg-white dark:bg-gray-900 rounded-full w-28 h-28">
              <span className="text-4xl font-bold bg-linear-to-r from-gray-700 to-gray-900 dark:from-gray-100 dark:to-gray-300 bg-clip-text text-transparent">
                {score}
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">/ 100</span>
            </div>
          </div>
          <p className={`mt-4 text-xl font-semibold ${risk.textColor}`}>
            {risk.level} Risk
          </p>
        </div>

        {/* Component Scores */}
        {componentScores && (
          <div className="space-y-4">
            <h4 className="font-medium text-sm text-gray-700 dark:text-gray-300">
              Risk Components
            </h4>
            {Object.entries(componentScores).map(([key, value]) => {
              const componentRisk = getRiskLevel(value);
              return (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="capitalize text-gray-700 dark:text-gray-300">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className={`font-semibold ${componentRisk.textColor}`}>
                      {value}%
                    </span>
                  </div>
                  <div className="relative">
                    <Progress value={value} className="h-2" />
                    <div 
                      className={`absolute top-0 left-0 h-2 rounded-full bg-linear-to-r ${componentRisk.color} transition-all`}
                      style={{ width: `${value}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
