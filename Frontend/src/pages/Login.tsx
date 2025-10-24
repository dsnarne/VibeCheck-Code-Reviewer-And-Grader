import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Code, Github, Mail, Loader2, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const Login = () => {
  const { signInWithGoogle, signInWithGitHub, signInWithEmail, signUpWithEmail, loading } = useAuth();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isGitHubLoading, setIsGitHubLoading] = useState(false);
  const [isEmailLoading, setIsEmailLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setError("");
    try {
      await signInWithGoogle();
    } catch (error: any) {
      setError(error.message || 'Google sign-in failed');
    } finally {
      setIsGoogleLoading(false);
    }
  };

  const handleGitHubSignIn = async () => {
    setIsGitHubLoading(true);
    setError("");
    try {
      await signInWithGitHub();
    } catch (error: any) {
      setError(error.message || 'GitHub sign-in failed');
    } finally {
      setIsGitHubLoading(false);
    }
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    setIsEmailLoading(true);
    setError("");

    try {
      if (isSignUp) {
        await signUpWithEmail(email, password, name);
        setError("Check your email for a confirmation link!");
      } else {
        await signInWithEmail(email, password);
      }
    } catch (error: any) {
      setError(error.message || `${isSignUp ? 'Sign up' : 'Sign in'} failed`);
    } finally {
      setIsEmailLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/95 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-4">
            <Code className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold">VibeCheck</h1>
          <p className="text-muted-foreground mt-2">
            AI-powered code quality analysis for GitHub repositories
          </p>
        </div>

        {/* Login Card */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle>{isSignUp ? "Create Account" : "Welcome Back"}</CardTitle>
            <CardDescription>
              {isSignUp 
                ? "Sign up to start analyzing your repositories" 
                : "Sign in to analyze your repositories and track code quality"
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Email/Password Form */}
            <form onSubmit={handleEmailAuth} className="space-y-4">
              {isSignUp && (
                <div>
                  <Input
                    type="text"
                    placeholder="Full Name (optional)"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="h-12"
                  />
                </div>
              )}
              
              <div>
                <Input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-12"
                  required
                />
              </div>
              
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-12 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              {error && (
                <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                disabled={isEmailLoading || isGoogleLoading || isGitHubLoading}
                className="w-full h-12 text-base"
              >
                {isEmailLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                ) : null}
                {isSignUp ? "Create Account" : "Sign In"}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            {/* OAuth Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <Button
                onClick={handleGitHubSignIn}
                disabled={isGitHubLoading || isGoogleLoading || isEmailLoading}
                className="h-12 text-base"
                variant="outline"
              >
                {isGitHubLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Github className="h-5 w-5" />
                )}
              </Button>

              <Button
                onClick={handleGoogleSignIn}
                disabled={isGoogleLoading || isGitHubLoading || isEmailLoading}
                className="h-12 text-base"
                variant="outline"
              >
                {isGoogleLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Mail className="h-5 w-5" />
                )}
              </Button>
            </div>

            {/* Toggle Sign In/Sign Up */}
            <div className="text-center">
              <button
                onClick={() => {
                  setIsSignUp(!isSignUp);
                  setError("");
                  setEmail("");
                  setPassword("");
                  setName("");
                }}
                className="text-sm text-primary hover:underline"
              >
                {isSignUp 
                  ? "Already have an account? Sign in" 
                  : "Don't have an account? Sign up"
                }
              </button>
            </div>

            {/* Info Text */}
            <div className="text-center pt-2">
              <p className="text-xs text-muted-foreground">
                By signing in, you agree to our terms of service and privacy policy.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Features Preview */}
        <div className="mt-8 grid grid-cols-1 gap-4 text-center">
          <div className="text-sm text-muted-foreground">
            <strong>What you'll get:</strong>
          </div>
          <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
            <div>• AI-powered code analysis</div>
            <div>• Quality scoring across 6 dimensions</div>
            <div>• Team contribution insights</div>
            <div>• Security vulnerability detection</div>
            <div>• Style consistency checks</div>
            <div>• Git hygiene analysis</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
