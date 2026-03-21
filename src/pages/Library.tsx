import { useState } from 'react';
import { ScientificFeedItem } from '@/components/library/ScientificFeedItem';
import { mockScientificFeeds } from '@/data/mockData';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, RefreshCw, BookOpen, Newspaper, FileText, Loader2 } from 'lucide-react';

export default function Library() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Simulate refresh - ready for API connection
    setTimeout(() => setIsRefreshing(false), 1500);
  };

  const filteredFeeds = mockScientificFeeds.filter(feed => {
    const matchesSearch = feed.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      feed.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      feed.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTab = activeTab === 'all' || feed.category.toLowerCase() === activeTab;
    return matchesSearch && matchesTab;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <BookOpen className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Biblioteca Científica</h1>
            <p className="text-muted-foreground mt-0.5">Actualizaciones en tiempo real</p>
          </div>
        </div>
        <Button 
          variant="outline" 
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="gap-2"
        >
          {isRefreshing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Actualizar
        </Button>
      </div>
      
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Buscar artículos, revistas o temas..."
          className="pl-10"
        />
      </div>
      
      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-secondary/50">
          <TabsTrigger value="all" className="gap-2">
            <Newspaper className="h-4 w-4" />
            Todo
          </TabsTrigger>
          <TabsTrigger value="research" className="gap-2">
            <FileText className="h-4 w-4" />
            Investigación
          </TabsTrigger>
          <TabsTrigger value="guidelines" className="gap-2">
            <BookOpen className="h-4 w-4" />
            Guías
          </TabsTrigger>
          <TabsTrigger value="technology" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Tecnología
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value={activeTab} className="mt-6">
          {/* New Articles Badge */}
          {filteredFeeds.some(f => f.isNew) && (
            <div className="flex items-center gap-2 mb-4 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse-subtle" />
              <span className="text-sm font-medium text-primary">
                {filteredFeeds.filter(f => f.isNew).length} nuevos artículos disponibles
              </span>
            </div>
          )}
          
          {/* Feed List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredFeeds.map((feed) => (
              <ScientificFeedItem
                key={feed.id}
                feed={feed}
                onClick={(f) => console.log('Selected feed:', f)}
              />
            ))}
          </div>
          
          {filteredFeeds.length === 0 && (
            <div className="text-center py-12">
              <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No se encontraron artículos</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
      
      {/* Sources */}
      <div className="pt-6 border-t border-border">
        <h3 className="text-sm font-medium text-foreground mb-3">Fuentes Integradas</h3>
        <div className="flex flex-wrap gap-2">
          {['The Lancet Psychiatry', 'JAMA Psychiatry', 'APA Journals', 'Nature Digital Medicine', 'NEJM'].map((source) => (
            <span 
              key={source}
              className="px-3 py-1.5 rounded-full text-xs font-medium bg-secondary text-secondary-foreground"
            >
              {source}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
