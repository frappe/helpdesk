import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send } from 'lucide-react';
import { useTicketStore } from '@/stores/ticketStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { formatDateTime, getInitials } from '@/lib/utils';

export function CustomerTicketDetail() {
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
      <div>
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-6" />
        <div className="h-96 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    );
  }

  if (!currentTicket) {
    return (
      <Card className="p-12 text-center">
        <p className="text-muted-foreground">Ticket not found</p>
      </Card>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/my-tickets"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to my tickets
        </Link>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{currentTicket.subject}</h1>
              <Badge>{currentTicket.status}</Badge>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="font-mono">{currentTicket.name}</span>
              <span>•</span>
              <span>Created {formatDateTime(currentTicket.creation)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Conversation */}
      <div className="space-y-6 max-w-3xl">
        {/* Original message */}
        <Card>
          <CardHeader>
            <div className="flex items-start gap-3">
              <Avatar>
                <AvatarFallback className="bg-primary text-white">
                  {currentTicket.raised_by ? getInitials(currentTicket.raised_by) : 'Y'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="font-medium">You</p>
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
          <CardContent className="pt-6">
            <div className="space-y-4">
              <textarea
                className="w-full min-h-[120px] px-3 py-2 text-sm border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Type your reply..."
                value={reply}
                onChange={(e) => setReply(e.target.value)}
              />
              <div className="flex justify-end">
                <Button size="sm">
                  <Send className="h-4 w-4 mr-2" />
                  Send Reply
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
