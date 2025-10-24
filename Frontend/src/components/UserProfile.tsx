import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { User, LogOut, Github } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const UserProfile = () => {
  const { user, authUser, signOut } = useAuth();

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <div className="font-semibold">
                {user?.name || authUser?.user_metadata?.name || 'User'}
              </div>
              {user?.github_username && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Github className="h-3 w-3" />
                  {user.github_username}
                </div>
              )}
            </div>
          </div>
          <Button
            onClick={signOut}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default UserProfile;
