/** Declaração mínima do process.env (sem depender de @types/node). */
declare const process: {
  env: {
    EXPO_PUBLIC_BASE_URL?: string;
    NODE_ENV?: string;
  };
};
