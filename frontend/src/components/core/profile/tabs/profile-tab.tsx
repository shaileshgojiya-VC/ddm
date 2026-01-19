import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ProfileTab() {
  // Static data - will be replaced with API data later
  const profileData = {
    fullName: "John Doe",
    email: "john.doe@danadairy.com",
    role: "Sales Manager",
    organization: "Dana Dairy EMEA",
    memberSince: "15/06/2023",
    avatarInitials: "JD",
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle className="text-2xl font-semibold">
            Profile Information
          </CardTitle>
        </div>
        <CardDescription>
          Your personal information and account details
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* User Avatar and Basic Info */}
        <div className="flex items-start gap-4">
          <Avatar className="size-20 bg-primary">
            <AvatarFallback className="bg-primary text-primary-foreground text-lg">
              {profileData.avatarInitials}
            </AvatarFallback>
          </Avatar>
          <div className="space-y-1">
            <h3 className="text-lg font-semibold">{profileData.fullName}</h3>
            <p className="text-sm text-muted-foreground">{profileData.role}</p>
            <Badge variant="secondary" className="mt-1">
              {profileData.organization}
            </Badge>
          </div>
        </div>
        {/* Divider */}
        <div className="border-t" />

        {/* Form Fields - Two Column Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                value={profileData.fullName}
                disabled
                className="bg-muted"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={profileData.role}
                disabled
                className="bg-muted"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="memberSince">Member Since</Label>
              <Input
                id="memberSince"
                value={profileData.memberSince}
                disabled
                className="bg-muted"
              />
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={profileData.email}
                disabled
                className="bg-muted"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="organization">Organization</Label>
              <Input
                id="organization"
                value={profileData.organization}
                disabled
                className="bg-muted"
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
