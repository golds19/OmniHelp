import { LightningIcon } from './Icons';

interface HeaderProps {
  isDark: boolean;
}

export const Header = ({ isDark }: HeaderProps) => {
  return (
    <div className="text-center mb-12">
      <h1 className={`text-4xl font-bold mb-3 ${isDark ? 'text-white' : 'text-slate-800'}`}>
        Agentic Document Intelligence 🤖
      </h1>
      <p className={`text-lg ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
        Upload documents and query them with ReAct AI Agent
      </p>
      <div
        className={`mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
          isDark ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-100 text-blue-700'
        }`}
      >
        <LightningIcon className="w-4 h-4" />
        Powered by ReAct Agent
      </div>
    </div>
  );
};
