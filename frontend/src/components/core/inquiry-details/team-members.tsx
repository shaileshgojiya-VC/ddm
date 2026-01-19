"use client";

import { Crown, Users, X } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Inquiry, UserDetail } from "@/types/inquiry";
import NoDataFound from "@/components/core/no-data-found";

// Helper function to generate initials from name
const getInitials = (name: string): string => {
  return name
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase())
    .join("")
    .slice(0, 2);
};

interface TeamMembersProps {
  readonly inquiryDetails: Inquiry;
}

export default function TeamMembers({ inquiryDetails }: TeamMembersProps) {
  const { user_details } = inquiryDetails || {};

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [teamMembers, setTeamMembers] = useState<UserDetail[]>(
    user_details || []
  );
  const [selectedMemberId, setSelectedMemberId] = useState<string>("");

  // Mock available members - this should come from your API
  const availableMembers: UserDetail[] = [];

  // Get available members that are not already in the team
  const getAvailableMembers = () => {
    const assignedIds = new Set(teamMembers.map((member) => member.id));
    return (
      availableMembers?.filter((member) => !assignedIds.has(member.id)) || []
    );
  };

  const handleAddMember = () => {
    if (!selectedMemberId) return;

    const memberToAdd = availableMembers?.find(
      (member) => member.id === selectedMemberId
    );

    if (memberToAdd) {
      const newMember: UserDetail = {
        ...memberToAdd,
        role_type: "observer",
      };
      setTeamMembers([...teamMembers, newMember]);
      setSelectedMemberId("");
    }
  };

  const handleRemoveMember = (memberId: string) => {
    setTeamMembers(teamMembers.filter((member) => member.id !== memberId));
  };

  const handleSetResponsible = (memberId: string) => {
    setTeamMembers(
      teamMembers.map((member) => ({
        ...member,
        role_type: member.id === memberId ? "responsible" : "observer",
      }))
    );
  };

  const handleSaveChanges = () => {
    // Save changes to API
    // console.log("Team members updated:", teamMembers);
    setIsDialogOpen(false);
  };

  const responsibleMember = teamMembers.find(
    (member) => member.role_type === "responsible"
  );
  const observers = teamMembers.filter(
    (member) => member.role_type !== "responsible"
  );
  const observerCount = observers.length;

  // If no team members at all, don't render anything
  if (!teamMembers || teamMembers.length === 0) {
    return null;
  }

  if (!user_details || user_details?.length === 0) {
    return (
      <NoDataFound
        title="No team members assigned"
        description="No team members assigned to this inquiry"
      />
    );
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-3 px-3 py-2 bg-muted/30 rounded-lg">
        {responsibleMember ? (
          <>
            <div className="flex items-center gap-2">
              <Avatar className="size-8 bg-primary">
                <AvatarFallback className="bg-primary text-white text-sm font-medium">
                  {getInitials(responsibleMember.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">
                  Responsible
                </span>
                <span className="text-sm font-medium">
                  {responsibleMember.name}
                </span>
              </div>
            </div>
            {observerCount > 0 && (
              <>
                <div className="size-1 rounded-full bg-muted-foreground/30" />
                <span className="text-xs text-muted-foreground">
                  +{observerCount} observer{observerCount === 1 ? "" : "s"}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 rounded-full border-2 border-dashed border-muted-foreground/30 text-muted-foreground"
                  onClick={() => setIsDialogOpen(true)}
                  disabled
                >
                  <Users className="size-4" />
                </Button>
              </>
            )}
          </>
        ) : (
          <>
            <span className="text-xs text-muted-foreground">
              {observerCount} observer{observerCount === 1 ? "" : "s"}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="size-8 rounded-full border-2 border-dashed border-muted-foreground/30 text-muted-foreground"
              onClick={() => setIsDialogOpen(true)}
              disabled
            >
              <Users className="size-4" />
            </Button>
          </>
        )}
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="size-5" />
              Manage Team Members
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Assigned Team Section */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold">Assigned Team</h3>
              <div className="space-y-2">
                {teamMembers.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    No team members assigned
                  </p>
                ) : (
                  teamMembers.map((member) => (
                    <div
                      key={member.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border ${
                        member.role_type === "responsible"
                          ? "bg-primary/5 border-primary/20"
                          : "bg-background"
                      }`}
                    >
                      <Avatar
                        className={`size-10 ${
                          member.role_type === "responsible"
                            ? "bg-primary"
                            : "bg-muted"
                        }`}
                      >
                        <AvatarFallback
                          className={`${
                            member.role_type === "responsible"
                              ? "bg-primary text-white"
                              : "bg-muted text-foreground"
                          } text-sm font-medium`}
                        >
                          {getInitials(member.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{member.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {member.role}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {member.role_type === "responsible" ? (
                          <div className="flex items-center gap-1.5 text-sm">
                            <Crown className="size-4 text-primary" />
                            <span className="text-muted-foreground">
                              Responsible
                            </span>
                          </div>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSetResponsible(member.id)}
                            className="h-8 text-xs"
                          >
                            Set Responsible
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-8"
                          onClick={() => handleRemoveMember(member.id)}
                        >
                          <X className="size-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Add Team Member Section */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold">Add Team Member</h3>
              <div className="flex gap-2">
                <Select
                  value={selectedMemberId}
                  onValueChange={setSelectedMemberId}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a team member to add..." />
                  </SelectTrigger>
                  <SelectContent>
                    {getAvailableMembers().length === 0 ? (
                      <div className="py-2 px-2 text-sm text-muted-foreground text-center">
                        No available members
                      </div>
                    ) : (
                      getAvailableMembers().map((member) => (
                        <SelectItem key={member.id} value={member.id}>
                          <div className="flex items-center gap-2">
                            <Avatar className="size-6 bg-muted">
                              <AvatarFallback className="bg-muted text-foreground text-xs">
                                {getInitials(member.name)}
                              </AvatarFallback>
                            </Avatar>
                            <span>{member.name}</span>
                            <span className="text-muted-foreground">
                              ({member.role})
                            </span>
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                {selectedMemberId && (
                  <Button onClick={handleAddMember} size="default">
                    Add
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Dialog Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveChanges}>Save Changes</Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
