import useSWRMutation from "swr/mutation";
import { authorizePayment, type AuthorizeResponse } from "@/lib/payments";

interface AuthorizeArgs {
  amount: number;
  currency: string;
}

async function authorize(
  _key: string,
  { arg }: { arg: AuthorizeArgs },
): Promise<AuthorizeResponse> {
  return authorizePayment(arg.amount, arg.currency);
}

export function useAuthorize() {
  const { trigger, data, error, isMutating } = useSWRMutation(
    "payments/authorize",
    authorize,
  );

  return {
    authorize: trigger,
    data,
    error: error as Error | undefined,
    isLoading: isMutating,
  };
}
