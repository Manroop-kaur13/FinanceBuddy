import { accounts, budgets, bills, transactions } from '../data/finance';
// Replace these async adapters with API calls without changing the UI.
export const financeService={ async getTransactions(){return transactions;},async getAccounts(){return accounts;},async getBudgets(){return budgets;},async getBills(){return bills;} };
