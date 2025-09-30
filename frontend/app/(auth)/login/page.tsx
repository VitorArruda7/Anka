"use client";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/axios";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "react-hot-toast";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email({ message: "Informe um e-mail válido" }),
  password: z.string().min(6, { message: "A senha precisa ter pelo menos 6 caracteres" }),
});

const registerSchema = loginSchema.extend({
  name: z.string().min(2, { message: "O nome precisa ter pelo menos 2 caracteres" }),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;
type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, loading } = useAuth();
  const [mode, setMode] = useState<Mode>("login");

  const {
    register: registerLogin,
    handleSubmit: handleLoginSubmit,
    formState: { errors: loginErrors, isSubmitting: isLoggingIn },
    reset: resetLogin,
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const {
    register: registerSignup,
    handleSubmit: handleRegisterSubmit,
    formState: { errors: registerErrors, isSubmitting: isRegistering },
    reset: resetRegister,
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "" },
  });

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, loading, router]);

  const authenticate = (token: string, message: string) => {
    login(token);
    toast.success(message);
    router.push("/dashboard");
  };

  const onLoginSubmit = async (values: LoginValues) => {
    try {
      const response = await api.post("/auth/login", values);
      authenticate(response.data.access_token, "Bem-vindo de volta!");
    } catch (error) {
      toast.error("Não foi possível entrar. Confira suas credenciais.");
    }
  };

  const onRegisterSubmit = async (values: RegisterValues) => {
    try {
      await api.post("/auth/register", values);
      const response = await api.post("/auth/login", {
        email: values.email,
        password: values.password,
      });
      authenticate(response.data.access_token, "Conta criada com sucesso!");
    } catch (error) {
      toast.error("Não foi possível criar a conta.");
    }
  };

  const toggleMode = () => {
    setMode((prev) => (prev === "login" ? "register" : "login"));
    resetLogin();
    resetRegister();
  };

  return (
    <Card className="w-full max-w-md space-y-6">
      <CardHeader className="space-y-3">
        <div className="space-y-1">
          <CardTitle>{mode === "login" ? "Entrar" : "Criar conta"}</CardTitle>
          <CardDescription>
            {mode === "login"
              ? "Acesse o cockpit do escritório Anka para acompanhar sua base de clientes."
              : "Preencha seus dados para começar a usar a plataforma Anka."}
          </CardDescription>
        </div>
        <Button type="button" variant="ghost" className="self-start px-0 text-sm" onClick={toggleMode}>
          {mode === "login" ? "Ainda não tem conta? Cadastre-se" : "Já possui conta? Entrar"}
        </Button>
      </CardHeader>
      {mode === "login" ? (
        <form className="space-y-4" onSubmit={handleLoginSubmit(onLoginSubmit)}>
          <div className="space-y-2">
            <Label htmlFor="login-email">E-mail</Label>
            <Input
              id="login-email"
              type="email"
              placeholder="voce@exemplo.com"
              autoComplete="email"
              {...registerLogin("email")}
            />
            {loginErrors.email && <p className="text-sm text-negative">{loginErrors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="login-password">Senha</Label>
            <Input
              id="login-password"
              type="password"
              placeholder="******"
              autoComplete="current-password"
              {...registerLogin("password")}
            />
            {loginErrors.password && <p className="text-sm text-negative">{loginErrors.password.message}</p>}
          </div>
          <Button type="submit" className="w-full" disabled={isLoggingIn}>
            {isLoggingIn ? "Entrando..." : "Entrar"}
          </Button>
        </form>
      ) : (
        <form className="space-y-4" onSubmit={handleRegisterSubmit(onRegisterSubmit)}>
          <div className="space-y-2">
            <Label htmlFor="register-name">Nome completo</Label>
            <Input id="register-name" placeholder="Seu nome" autoComplete="name" {...registerSignup("name")} />
            {registerErrors.name && <p className="text-sm text-negative">{registerErrors.name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="register-email">E-mail</Label>
            <Input
              id="register-email"
              type="email"
              placeholder="voce@exemplo.com"
              autoComplete="email"
              {...registerSignup("email")}
            />
            {registerErrors.email && <p className="text-sm text-negative">{registerErrors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="register-password">Senha</Label>
            <Input
              id="register-password"
              type="password"
              placeholder="Mínimo de 6 caracteres"
              autoComplete="new-password"
              {...registerSignup("password")}
            />
            {registerErrors.password && <p className="text-sm text-negative">{registerErrors.password.message}</p>}
          </div>
          <Button type="submit" className="w-full" disabled={isRegistering}>
            {isRegistering ? "Criando conta..." : "Criar conta"}
          </Button>
        </form>
      )}
    </Card>
  );
}
