import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send, Paperclip, MoreVertical } from 'lucide-react';
import { useTicketStore } from '@/stores/ticketStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { formatDateTime, getInitials } from '@/lib/utils';

export function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const { currentTicket, isLoading, fetchTicket } = useTicketStore();
  const [reply, setReply] = useState('');

  useEffect(() => {
    if (id) {
      fetchTicket(id);
    }
  }, [id, fetchTicket]);

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-6" />
        <div className="h-96 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    );
  }

  if (!currentTicket) {
    return (
      <div className="p-8">
        <Card className="p-12 text-center">
          <p className="text-muted-foreground">Ticket not found</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <Link to="/tickets" className="inline-flex items-center text-sm text-muted-foreground hover:text-gray-900 mb-4">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to tickets
        </Link>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{currentTicket.subject}</h1>
              <Badge>{currentTicket.status}</Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="font-mono">{currentTicket.name}</span>
              <span>•</span>
              <span>Created {formatDateTime(currentTicket.creation)}</span>
              {currentTicket.customer && (
                <>
                  <span>•</span>
                  <span>Customer: {currentTicket.customer}</span>
                </>
              )}
            </div>
          </div>
          <Button variant="outline" size="icon">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <div className="flex items-start gap-3">
                <Avatar>
                  <AvatarFallback className="bg-primary text-white">
                    {currentTicket.raised_by ? getInitials(currentTicket.raised_by) : 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-medium">{currentTicket.raised_by || 'Customer'}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDateTime(currentTicket.creation)}
                      </p>
                    </div>
                  </div>
                  <div className="prose prose-sm max-w-none">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {currentTicket.description || 'No description provided'}
                    </p>
                  </div>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Reply box */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Reply to ticket</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <textarea
                  className="w-full min-h-[120px] px-3 py-2 text-sm border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Type your reply..."
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                />
                <div className="flex items-center justify-between">
                  <Button variant="outline" size="sm">
                    <Paperclip className="h-4 w-4 mr-2" />
                    Attach files
                  </Button>
                  <Button size="sm">
                    <Send className="h-4 w-4 mr-2" />
                    Send Reply
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground mb-1">Status</p>
                <Badge>{currentTicket.status}</Badge>
              </div>
              {currentTicket.priority && (
                <div>
                  <p className="text-muted-foreground mb-1">Priority</p>
                  <Badge variant="warning">{currentTicket.priority}</Badge>
                </div>
              )}
              {currentTicket.ticket_type && (
                <div>
                  <p className="text-muted-foreground mb-1">Type</p>
                  <p className="font-medium">{currentTicket.ticket_type}</p>
                </div>
              )}
              {currentTicket.assigned_to && (
                <div>
                  <p className="text-muted-foreground mb-1">Assigned to</p>
                  <p className="font-medium">{currentTicket.assigned_to}</p>
                </div>
              )}
              {currentTicket.agent_group && (
                <div>
                  <p className="text-muted-foreground mb-1">Team</p>
                  <p className="font-medium">{currentTicket.agent_group}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
