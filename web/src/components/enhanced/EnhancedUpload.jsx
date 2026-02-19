import React from 'react';
import { Upload, FileText, Shield } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';

export default function EnhancedUpload({ onFileSelect, isScanning }) {
  const [isDragging, setIsDragging] = React.useState(false);
  const fileInputRef = React.useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <div className="flex justify-center mb-4">
          <div className="rounded-full bg-linear-to-br from-blue-500 to-cyan-400 p-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
        </div>
        <CardTitle className="text-3xl font-bold bg-linear-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
          Security Scanner
        </CardTitle>
        <CardDescription className="text-base">
          Upload your Infrastructure as Code files for comprehensive security analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300
            ${isDragging 
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20 scale-105' 
              : 'border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-600'
            }
            ${isScanning ? 'opacity-50 pointer-events-none' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept=".tf,.yaml,.yml,.json"
            disabled={isScanning}
          />
          
          <div className="flex flex-col items-center gap-4">
            <div className={`rounded-full p-4 ${isDragging ? 'bg-blue-100 dark:bg-blue-900' : 'bg-gray-100 dark:bg-gray-800'} transition-colors`}>
              {isDragging ? (
                <FileText className="w-10 h-10 text-blue-500" />
              ) : (
                <Upload className="w-10 h-10 text-gray-500 dark:text-gray-400" />
              )}
            </div>
            
            <div className="space-y-2">
              <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                {isDragging ? 'Drop your file here' : 'Drag & drop your file here'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                or
              </p>
              <Button
                onClick={handleBrowseClick}
                disabled={isScanning}
                size="lg"
                className="bg-linear-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600"
              >
                Browse Files
              </Button>
            </div>
            
            <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
              <p>Supported formats: Terraform (.tf), Kubernetes (.yaml, .yml), JSON</p>
              <p className="font-medium">Maximum file size: 10MB</p>
            </div>
          </div>
        </div>

        {isScanning && (
          <div className="mt-6 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-950/20 rounded-full">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
                Scanning in progress...
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
