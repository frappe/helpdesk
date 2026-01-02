import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import { useTicketStore } from '@/stores/ticketStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { formatRelativeTime } from '@/lib/utils';

const STATUS_COLORS: Record<string, 'default' | 'success' | 'warning' | 'secondary'> = {
  'Open': 'default',
  'Replied': 'warning',
  'Resolved': 'success',
  'Closed': 'secondary',
};

export function CustomerTickets() {
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
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Support Tickets</h1>
          <p className="text-muted-foreground mt-1">
            View and manage your support requests
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Ticket
        </Button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="search"
            placeholder="Search your tickets..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Ticket list */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredTickets.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="max-w-sm mx-auto">
            <p className="text-lg font-medium text-gray-900 mb-2">No tickets yet</p>
            <p className="text-muted-foreground mb-6">
              Create your first support ticket to get help from our team
            </p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Ticket
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTickets.map((ticket) => (
            <Link key={ticket.name} to={`/my-tickets/${ticket.name}`}>
              <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-muted-foreground font-mono">
                        {ticket.name}
                      </span>
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      {ticket.subject}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Created {formatRelativeTime(ticket.creation)}
                      {ticket.assigned_to && ` • Assigned to ${ticket.assigned_to}`}
                    </p>
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
