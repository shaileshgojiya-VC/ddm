import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Eye, EyeOff } from "lucide-react";
import clientFetcher from "@/utils/fetcher/client";
import { useSession } from "next-auth/react";
import { signOut } from "next-auth/react";

interface ChangePasswordDialogProps {
    onSuccess?: () => void;
}

export function ChangePasswordDialog({ onSuccess }: ChangePasswordDialogProps) {
    const { data: session } = useSession();
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [showPasswords, setShowPasswords] = useState({
        current: false,
        new: false,
        confirm: false,
    });

    const [formData, setFormData] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });

    const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
        setShowPasswords((prev) => ({
            ...prev,
            [field]: !prev[field],
        }));
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
        setError("");
    };

    const validateForm = () => {
        if (!formData.current_password) {
            setError("Current password is required");
            return false;
        }
        if (!formData.new_password) {
            setError("New password is required");
            return false;
        }
        if (!formData.confirm_password) {
            setError("Password confirmation is required");
            return false;
        }
        if (formData.new_password !== formData.confirm_password) {
            setError("New passwords do not match");
            return false;
        }
        if (formData.new_password.length < 8) {
            setError("Password must be at least 8 characters");
            return false;
        }
        // Check password strength: uppercase, lowercase, digit, special char
        const hasUpper = /[A-Z]/.test(formData.new_password);
        const hasLower = /[a-z]/.test(formData.new_password);
        const hasDigit = /\d/.test(formData.new_password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(
            formData.new_password
        );

        if (!hasUpper || !hasLower || !hasDigit || !hasSpecial) {
            setError(
                "Password must contain uppercase, lowercase, number, and special character"
            );
            return false;
        }
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validateForm()) return;

        setLoading(true);
        try {
            const response = await clientFetcher({
                request: "auth/password/change-v2",
                method: "POST",
                payload: formData,
                token: session?.accessToken || "",
            });

            if (response.status === "success") {
                setSuccess(true);
                setFormData({
                    current_password: "",
                    new_password: "",
                    confirm_password: "",
                });

                // Auto-logout after 2 seconds to force re-login with new password
                setTimeout(() => {
                    signOut({ redirect: true, callbackUrl: "/login" });
                }, 2000);

                onSuccess?.();
            } else {
                setError(response.message || "Failed to change password");
            }
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "An error occurred while changing password"
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                    Change Password
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Change Password</DialogTitle>
                    <DialogDescription>
                        Enter your current password and a new password to proceed.
                    </DialogDescription>
                </DialogHeader>

                {error && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {success && (
                    <Alert className="border-green-600 bg-green-50">
                        <AlertCircle className="h-4 w-4 text-green-600" />
                        <AlertDescription className="text-green-800">
                            Password changed successfully! You will be logged out shortly.
                        </AlertDescription>
                    </Alert>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Current Password */}
                    <div className="space-y-2">
                        <Label htmlFor="current_password">Current Password</Label>
                        <div className="relative">
                            <Input
                                id="current_password"
                                name="current_password"
                                type={showPasswords.current ? "text" : "password"}
                                placeholder="Enter current password"
                                value={formData.current_password}
                                onChange={handleInputChange}
                                disabled={loading}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => togglePasswordVisibility("current")}
                                className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                            >
                                {showPasswords.current ? (
                                    <EyeOff className="h-4 w-4" />
                                ) : (
                                    <Eye className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                    </div>

                    {/* New Password */}
                    <div className="space-y-2">
                        <Label htmlFor="new_password">New Password</Label>
                        <div className="relative">
                            <Input
                                id="new_password"
                                name="new_password"
                                type={showPasswords.new ? "text" : "password"}
                                placeholder="Enter new password"
                                value={formData.new_password}
                                onChange={handleInputChange}
                                disabled={loading}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => togglePasswordVisibility("new")}
                                className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                            >
                                {showPasswords.new ? (
                                    <EyeOff className="h-4 w-4" />
                                ) : (
                                    <Eye className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Must be 8+ characters with uppercase, lowercase, number, and
                            special character
                        </p>
                    </div>

                    {/* Confirm Password */}
                    <div className="space-y-2">
                        <Label htmlFor="confirm_password">Confirm Password</Label>
                        <div className="relative">
                            <Input
                                id="confirm_password"
                                name="confirm_password"
                                type={showPasswords.confirm ? "text" : "password"}
                                placeholder="Confirm new password"
                                value={formData.confirm_password}
                                onChange={handleInputChange}
                                disabled={loading}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => togglePasswordVisibility("confirm")}
                                className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                            >
                                {showPasswords.confirm ? (
                                    <EyeOff className="h-4 w-4" />
                                ) : (
                                    <Eye className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => setOpen(false)}
                            disabled={loading}
                        >
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading || success}>
                            {loading ? "Changing..." : "Change Password"}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
