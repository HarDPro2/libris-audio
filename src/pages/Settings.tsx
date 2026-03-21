import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { User, Bell, Shield, Database, Save } from 'lucide-react';

export default function Settings() {
  const [notifications, setNotifications] = useState({
    appointments: true,
    updates: true,
    insights: false,
  });

  return (
    <div className="max-w-3xl space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Configuración</h1>
        <p className="text-muted-foreground mt-1">Gestione sus preferencias y cuenta</p>
      </div>
      
      {/* Profile Section */}
      <div className="stat-card">
        <div className="flex items-center gap-3 mb-6">
          <User className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Perfil Profesional</h2>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nombre Completo</Label>
            <Input id="name" defaultValue="Dr. Alberto Ramírez" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="specialty">Especialidad</Label>
            <Input id="specialty" defaultValue="Psicología Clínica" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="license">Número de Colegiado</Label>
            <Input id="license" defaultValue="PSI-28574" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" defaultValue="dr.ramirez@clinica.com" />
          </div>
        </div>
      </div>
      
      {/* Notifications Section */}
      <div className="stat-card">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Notificaciones</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">Recordatorios de Citas</p>
              <p className="text-sm text-muted-foreground">Recibir alertas antes de cada cita</p>
            </div>
            <Switch 
              checked={notifications.appointments}
              onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, appointments: checked }))}
            />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">Actualizaciones Científicas</p>
              <p className="text-sm text-muted-foreground">Nuevos artículos de la biblioteca</p>
            </div>
            <Switch 
              checked={notifications.updates}
              onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, updates: checked }))}
            />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">Insights de IA</p>
              <p className="text-sm text-muted-foreground">Sugerencias automáticas durante sesiones</p>
            </div>
            <Switch 
              checked={notifications.insights}
              onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, insights: checked }))}
            />
          </div>
        </div>
      </div>
      
      {/* Security Section */}
      <div className="stat-card">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Seguridad</h2>
        </div>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-password">Contraseña Actual</Label>
            <Input id="current-password" type="password" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="new-password">Nueva Contraseña</Label>
              <Input id="new-password" type="password" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirmar Contraseña</Label>
              <Input id="confirm-password" type="password" />
            </div>
          </div>
        </div>
      </div>
      
      {/* API Section */}
      <div className="stat-card">
        <div className="flex items-center gap-3 mb-6">
          <Database className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Integraciones API</h2>
        </div>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-key">Clave API (Servicios Externos)</Label>
            <Input id="api-key" type="password" placeholder="sk-..." />
            <p className="text-xs text-muted-foreground">Se usará para conectar con servicios de IA externos</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="webhook">Webhook URL</Label>
            <Input id="webhook" placeholder="https://..." />
            <p className="text-xs text-muted-foreground">Endpoint para notificaciones en tiempo real</p>
          </div>
        </div>
      </div>
      
      {/* Save Button */}
      <div className="flex justify-end">
        <Button className="gap-2">
          <Save className="h-4 w-4" />
          Guardar Cambios
        </Button>
      </div>
    </div>
  );
}
