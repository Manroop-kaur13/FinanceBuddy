export type Tx = { id:string; date:string; description:string; category:string; account:string; type:'Income'|'Expense'|'Transfer'; amount:number; note?:string };
export type Account = { id:string; name:string; kind:string; number:string; balance:number; tone:string };
export type Budget = { category:string; spent:number; limit:number; color:string };
export type Bill = { id:string; name:string; due:string; amount:number; status:'Upcoming'|'Due soon'|'Paid' };
