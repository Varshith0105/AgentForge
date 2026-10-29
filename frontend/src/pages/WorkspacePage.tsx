import React, { useState } from 'react';
import { FileExplorer } from '../components/workspace/FileExplorer';
import { CodeEditor } from '../components/workspace/CodeEditor';
import { TerminalPanel } from '../components/workspace/TerminalPanel';
import { StreamingChat } from '../components/chat/StreamingChat';

export const WorkspacePage: React.FC = () => {
  const [showBottomPanel, setShowBottomPanel] = useState(true);

  return (
    <div className="h-full flex flex-1 overflow-hidden bg-background">
      {/* File Explorer Sidebar */}
      <div className="w-60 flex-shrink-0">
        <FileExplorer />
      </div>

      {/* Main Editor & Terminal Stack */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 min-h-0">
          <CodeEditor />
        </div>
        {showBottomPanel && (
          <div className="h-48 flex-shrink-0 border-t border-border">
            <TerminalPanel onClose={() => setShowBottomPanel(false)} />
          </div>
        )}
      </div>

      {/* Right AI Streaming Chat Panel */}
      <div className="w-80 flex-shrink-0">
        <StreamingChat />
      </div>
    </div>
  );
};
