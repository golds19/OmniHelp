export const Header = () => {
  return (
    <div className="flex items-center gap-4">
      <div className="w-1 h-10 rounded-full bg-accent" />
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Document Intelligence</h1>
        <p className="text-sm text-foreground-dim mt-0.5">Upload a PDF and query it with AI</p>
      </div>
    </div>
  );
};
