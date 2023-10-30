import { InjectionKey } from "vue";
import { Resource, Ticket as T } from "@/types";

export const Comments: InjectionKey<Resource> = Symbol("Comments");
export const ITicket: InjectionKey<Resource<T>> = Symbol("ITicket");
export const Id: InjectionKey<string> = Symbol("Id");
export const Ticket: InjectionKey<Resource> = Symbol("Ticket");
