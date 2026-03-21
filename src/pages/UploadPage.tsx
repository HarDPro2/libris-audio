import { Upload } from 'lucide-react';
import { UploadCard } from '@/components/libris/UploadCard';

export default function UploadPage() {
  return (
    <div className="animate-fade-in max-w-lg mx-auto mt-12">
      <div className="text-center mb-8">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/15 mb-4">
          <Upload className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">Subir PDF</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Selecciona un archivo PDF y lo convertiremos en audiolibro automáticamente.
        </p>
      </div>
      <div className="max-w-[200px] mx-auto">
        <UploadCard />
      </div>
    </div>
  );
}
