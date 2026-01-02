import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter } from 'lucide-react';
import { useTicketStore } from '@/stores/ticketStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { formatRelativeTime } from '@/lib/utils';

const STATUS_COLORS: Record<string, 'default' | 'success' | 'warning' | 'destructive'> = {
  'Open': 'default',
  'Replied': 'warning',
  'Resolved': 'success',
  'Closed': 'secondary',
};

const PRIORITY_COLORS: Record<string, 'default' | 'warning' | 'destructive'> = {
  'Low': 'default',
  'Medium': 'warning',
  'High': 'destructive',
  'Urgent': 'destructive',
};

export function TicketList() {
  const { tickets, isLoading, fetchTickets } = useTicketStore();
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const filteredTickets = tickets.filter((ticket) =>
    ticket.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ticket.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tickets</h1>
          <p className="text-muted-foreground mt-1">
            Manage and respond to customer support tickets
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Ticket
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="search"
            placeholder="Search tickets by subject or ID..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Ticket list */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredTickets.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-muted-foreground">No tickets found</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTickets.map((ticket) => (
            <Link key={ticket.name} to={`/tickets/${ticket.name}`}>
              <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-muted-foreground font-mono">
                        {ticket.name}
                      </span>
                      {ticket.priority && (
                        <Badge variant={PRIORITY_COLORS[ticket.priority] || 'default'} className="text-xs">
                          {ticket.priority}
                        </Badge>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1 truncate">
                      {ticket.subject}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {ticket.customer && (
                        <span>Customer: {ticket.customer}</span>
                      )}
                      {ticket.assigned_to && (
                        <span>• Assigned to: {ticket.assigned_to}</span>
                      )}
                      <span>• {formatRelativeTime(ticket.creation)}</span>
                    </div>
                  </div>
                  <Badge variant={STATUS_COLORS[ticket.status] || 'default'}>
                    {ticket.status}
                  </Badge>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
