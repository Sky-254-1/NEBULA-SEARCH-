import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, FileText, WifiOff, Loader2, Check } from 'lucide-react';
import { useDocumentStore } from '@/state';
import { useOfflineStore } from '@/state';
import { toast } from 'react-hot-toast';

export const OfflineLibraryPage: React.FC = () => {
  const { documents } = useDocumentStore();
  const { isOnline, queuedActions } = useOfflineStore();
  const [downloadingIds, setDownloadingIds] = useState<Set<number>>(new Set());

  const handleDownload = async (documentId: number, filename: string) => {
    try {
      setDownloadingIds(prev => new Set(prev).add(documentId));
      
      // In a real implementation, this would use the Cache API or IndexedDB
      // For now, we'll just show a success message
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success(`${filename} downloaded for offline use`);
    } catch (error) {
      toast.error('Failed to download document');
    } finally {
      setDownloadingIds(prev => {
        const next = new Set(prev);
        next.delete(documentId);
        return next;
      });
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Offline Library
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Access your documents offline
        </p>
      </div>

      {/* Status */}
      <div className={`flex items-center gap-3 p-4 rounded-xl ${
        isOnline 
          ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
          : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
      }`}>
        {isOnline ? (
          <>
            <WifiOff className="text-green-600 dark:text-green-400" size={24} />
            <div>
              <p className="font-medium text-green-900 dark:text-green-100">
                You're online
              </p>
              <p className="text-sm text-green-700 dark:text-green-300">
                Documents will sync automatically
              </p>
            </div>
          </>
        ) : (
          <>
            <WifiOff className="text-yellow-600 dark:text-yellow-400" size={24} />
            <div>
              <p className="font-medium text-yellow-900 dark:text-yellow-100">
                You're offline
              </p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                Access your downloaded documents below
              </p>
            </div>
          </>
        )}
      </div>

      {/* Queued Actions */}
      {queuedActions.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
            Pending Sync ({queuedActions.length})
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {queuedActions.length} action{queuedActions.length !== 1 ? 's' : ''} will be synced when you're back online
          </p>
        </div>
      )}

      {/* Downloaded Documents */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Downloaded Documents
          </h3>
          
          {documents.length > 0 ? (
            <div className="space-y-3">
              {documents.map((doc, index) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                      <FileText className="text-blue-600 dark:text-blue-400" size={24} />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {doc.filename}
                      </h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {doc.content_type || 'Unknown type'}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => handleDownload(doc.id, doc.filename)}
                    disabled={downloadingIds.has(doc.id)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {downloadingIds.has(doc.id) ? (
                      <>
                        <Loader2 className="animate-spin" size={18} />
                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download size={18} />
                        Download
                      </>
                    )}
                  </button>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Download className="mx-auto text-gray-400 mb-4" size={48} />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No documents downloaded
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Download documents to access them offline
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};