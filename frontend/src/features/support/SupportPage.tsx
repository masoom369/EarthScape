import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import { theme } from '../../styles/theme';
import type { SupportTicket } from '../../types/support';
import { TicketForm } from './TicketForm';
import { TicketList } from './TicketList';

export function SupportPage() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);

  const fetchTickets = useCallback(async () => {
    const { data } = await api.get('/support/tickets', { params: { limit: 50 } });
    setTickets(data.items);
  }, []);

  useEffect(() => { fetchTickets(); }, [fetchTickets]);

  return (
    <div>
      <h1 style={{ color: theme.colors.primary }}>Support</h1>
      <TicketForm onSubmitted={fetchTickets} />
      <TicketList tickets={tickets} />
    </div>
  );
}
