"use client";

import { useState, useEffect } from "react";
import { Loader2, Edit2, Check, X } from "lucide-react";
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
import { Button } from "@/components/ui/button";
import { ProfileImageUpload } from "@/components/core/profile/profile-image-upload";
import { getProfile, updateProfile } from "@/lib/profile-api";
import { formatDate } from "@/utils/date-format";
import { toast } from "sonner";
import { useSession } from "next-auth/react";
import type { Profile, UpdateProfileRequest } from "@/types/user";

export default function ProfileTab() {
  const { data: session } = useSession();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<UpdateProfileRequest>({
    name: "",
    phone_number: "",
    location: "",
  });

  useEffect(() => {
    if (session?.accessToken) {
      fetchProfile();
    }
  }, [session?.accessToken]);

  const fetchProfile = async () => {
    if (!session?.accessToken) {
      toast.error("Session expired. Please login again.");
      return;
    }

    try {
      setLoading(true);
      const profileData = await getProfile(session.accessToken);
      if (profileData) {
        setProfile(profileData);
        setFormData({
          name: profileData.name || "",
          phone_number: profileData.phone_number || "",
          location: profileData.location || "",
        });
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to load profile";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof UpdateProfileRequest, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async () => {
    if (!profile || !session?.accessToken) {
      toast.error("Session expired. Please login again.");
      return;
    }

    // Validate name is not empty
    if (!formData.name?.trim()) {
      toast.error("Name is required");
      return;
    }

    setSaving(true);

    try {
      const updatePayload: UpdateProfileRequest = {};

      // Only include changed fields
      if (formData.name !== profile.name) {
        updatePayload.name = formData.name;
      }
      if (formData.phone_number !== profile.phone_number) {
        updatePayload.phone_number = formData.phone_number || null;
      }
      if (formData.location !== profile.location) {
        updatePayload.location = formData.location || null;
      }

      // Check if there are any changes
      if (Object.keys(updatePayload).length === 0) {
        setIsEditing(false);
        return;
      }

      const updatedProfile = await updateProfile(updatePayload, session.accessToken);

      if (updatedProfile) {
        setProfile(updatedProfile);
        setIsEditing(false);
        toast.success("Profile updated successfully");
      } else {
        toast.error("Failed to update profile");
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to update profile";
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (profile) {
      setFormData({
        name: profile.name || "",
        phone_number: profile.phone_number || "",
        location: profile.location || "",
      });
    }
    setIsEditing(false);
  };

  const handleImageUploaded = (updatedProfile: Profile) => {
    setProfile(updatedProfile);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!profile) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          Failed to load profile data
        </CardContent>
      </Card>
    );
  }

  const profileCompleteness = profile.profile_completeness ?? 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-semibold">
              Profile Information
            </CardTitle>
            <CardDescription>
              Your personal information and account details
            </CardDescription>
          </div>
          {!isEditing && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              <Edit2 className="size-4" />
              Edit Profile
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Profile Image and Basic Info */}
        <div className="flex items-start gap-4">
          <ProfileImageUpload
            profile={profile}
            onImageUploaded={handleImageUploaded}
          />
          <div className="flex-1 space-y-2">
            <div>
              <h3 className="text-lg font-semibold">{profile.name}</h3>
              <p className="text-sm text-muted-foreground">{profile.email}</p>
            </div>
            {profileCompleteness > 0 && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Profile Completeness</span>
                  <span className="font-medium">{profileCompleteness}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${profileCompleteness}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Divider */}
        <div className="border-t" />

        {/* Form Fields - Two Column Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name *</Label>
              <Input
                id="name"
                value={formData.name || ""}
                onChange={(e) => handleInputChange("name", e.target.value)}
                disabled={!isEditing}
                className={!isEditing ? "bg-muted" : ""}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone_number">Phone Number</Label>
              <Input
                id="phone_number"
                type="tel"
                value={formData.phone_number || ""}
                onChange={(e) =>
                  handleInputChange("phone_number", e.target.value)
                }
                disabled={!isEditing}
                placeholder="Enter phone number"
                className={!isEditing ? "bg-muted" : ""}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="joined_at">Member Since</Label>
              <Input
                id="joined_at"
                value={formatDate(profile.joined_at)}
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
                value={profile.email}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground">
                Email cannot be changed from profile settings
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={formData.location || ""}
                onChange={(e) => handleInputChange("location", e.target.value)}
                disabled={!isEditing}
                placeholder="Enter location"
                className={!isEditing ? "bg-muted" : ""}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="updated_at">Last Updated</Label>
              <Input
                id="updated_at"
                value={formatDate(profile.updated_at)}
                disabled
                className="bg-muted"
              />
            </div>
          </div>
        </div>

        {/* Edit Mode Actions */}
        {isEditing && (
          <div className="flex items-center justify-end gap-2 border-t pt-4">
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={saving}
            >
              <X className="size-4" />
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="size-4" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
