import { InjectionKey } from "vue";
import { Resource, Ticket } from "@/types";

export const ITicket: InjectionKey<Resource<Ticket>> = Symbol("Ticket");
