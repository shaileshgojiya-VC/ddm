"use client";

import { useState, useRef } from "react";
import { Camera, Loader2 } from "lucide-react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useSession } from "next-auth/react";
import { uploadProfileImage } from "@/lib/profile-api";
import { toast } from "sonner";
import type { Profile } from "@/types/user";

interface ProfileImageUploadProps {
    profile: Profile | null;
    onImageUploaded?: (updatedProfile: Profile) => void;
}

const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function ProfileImageUpload({
    profile,
    onImageUploaded,
}: ProfileImageUploadProps) {
    const { data: session } = useSession();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [preview, setPreview] = useState<string | null>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
            toast.error(
                "Invalid file type. Please select a JPG, JPEG, PNG, GIF, or WEBP image."
            );
            return;
        }

        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
            toast.error("File size exceeds 10MB. Please select a smaller image.");
            return;
        }

        // Create preview
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreview(reader.result as string);
        };
        reader.readAsDataURL(file);

        // Upload file
        handleUpload(file);
    };

    const handleUpload = async (file: File) => {
        if (!session?.accessToken) {
            toast.error("Session expired. Please login again.");
            return;
        }

        setUploading(true);

        try {
            const updatedProfile = await uploadProfileImage(file, session.accessToken);

            if (updatedProfile) {
                toast.success("Profile image uploaded successfully");
                setPreview(null);
                onImageUploaded?.(updatedProfile);
            } else {
                toast.error("Failed to upload profile image");
            }
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : "Failed to upload profile image";
            toast.error(errorMessage);
        } finally {
            setUploading(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const getInitials = (name: string): string => {
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    const imageUrl = preview || profile?.profile_image_url || null;
    const displayName = profile?.name || "";

    return (
        <div className="relative inline-block">
            <Avatar className="size-20 bg-primary">
                {imageUrl ? (
                    <AvatarImage src={imageUrl} alt={displayName} />
                ) : null}
                <AvatarFallback className="bg-primary text-primary-foreground text-3xl font-semibold">
                    {displayName ? getInitials(displayName) : "U"}
                </AvatarFallback>
            </Avatar>

            <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_IMAGE_TYPES.join(",")}
                onChange={handleFileSelect}
                className="hidden"
                disabled={uploading}
            />

            <Button
                type="button"
                variant="outline"
                size="icon"
                className="absolute bottom-0 right-0 size-8 rounded-full border-2 border-background"
                onClick={handleClick}
                disabled={uploading}
                aria-label="Change profile image"
            >
                {uploading ? (
                    <Loader2 className="size-4 animate-spin" />
                ) : (
                    <Camera className="size-4" />
                )}
            </Button>
        </div>
    );
}

