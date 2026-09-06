export type PersonId = string;
export type AmountCents = number; // integer cents

export type Participant = {
  person: PersonId;
  weight?: number;
};

export type Expense = {
  id: string;
  description: string;
  amountCents: AmountCents;
  paidBy: PersonId;
  participants: Participant[];
};

export type BalanceMap = Record<PersonId, AmountCents>;

export type Transfer = {
  from: PersonId;
  to: PersonId;
  amountCents: AmountCents;
};
