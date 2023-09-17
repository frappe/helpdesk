import { InjectionKey, Ref } from "vue";
import { Resource, Column } from "@/types";

type I = {
  name: string;
  [key: string]: unknown;
};
type R = Resource<Array<I>>;
export const CheckboxKey: InjectionKey<boolean> = Symbol("Checkbox");
export const ColumnsKey: InjectionKey<Array<Column>> = Symbol("Columns");
export const DocTypeKey: InjectionKey<string> = Symbol("DocType");
export const FilterKey: InjectionKey<boolean> = Symbol("Filter");
export const IdKey: InjectionKey<string> = Symbol("Id");
export const PluralKey: InjectionKey<Ref<string>> = Symbol("Plural");
export const ResourceKey: InjectionKey<R> = Symbol("Resource");
export const SingluarKey: InjectionKey<Ref<string>> = Symbol("Singular");
