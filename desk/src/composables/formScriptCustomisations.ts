import { Ticket } from "@/types";
import { isCustomerPortal } from "@/utils";

function createFormContext(data){
	return {
		doc:data
	}
}

function updateField