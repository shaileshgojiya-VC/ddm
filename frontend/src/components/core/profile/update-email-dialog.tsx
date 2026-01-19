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

interface UpdateEmailDialogProps {
    currentEmail: string;
    onSuccess?: () => void;
}

export function UpdateEmailDialog({
    currentEmail,
    onSuccess,
}: UpdateEmailDialogProps) {
    const { data: session } = useSession();
    const [open, setOpen] = useState(false);
    const [step, setStep] = useState<"initiate" | "verify" | "confirm">(
        "initiate"
    );
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const [formData, setFormData] = useState({
        new_email: "",
        current_password: "",
        email_token: "",
        confirmation_token: "",
    });

    const [pendingEmail, setPendingEmail] = useState("");

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
        setError("");
    };

    const validateEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const handleInitiate = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.new_email) {
            setError("New email is required");
            return;
        }

        if (!validateEmail(formData.new_email)) {
            setError("Please enter a valid email address");
            return;
        }

        if (formData.new_email === currentEmail) {
            setError("New email must be different from current email");
            return;
        }

        if (!formData.current_password) {
            setError("Current password is required");
            return;
        }

        setLoading(true);
        try {
            const response = await clientFetcher({
                request: "auth/email/initiate",
                method: "POST",
                payload: {
                    new_email: formData.new_email,
                    current_password: formData.current_password,
                },
                token: session?.accessToken || "",
            });

            if (response.status === "success") {
                setPendingEmail(formData.new_email);
                setStep("verify");
                setError("");
            } else {
                setError(
                    response.message || "Failed to initiate email update. Please try again."
                );
            }
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "An error occurred while updating email"
            );
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.email_token) {
            setError("Verification token is required");
            return;
        }

        setLoading(true);
        try {
            const response = await clientFetcher({
                request: `auth/email/verify?token=${encodeURIComponent(
                    formData.email_token
                )}`,
                method: "GET",
                token: session?.accessToken || "",
            });

            if (response.status === "success") {
                setStep("confirm");
                setError("");
            } else {
                setError(response.message || "Invalid or expired verification token");
            }
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "An error occurred during verification"
            );
        } finally {
            setLoading(false);
        }
    };

    const handleConfirm = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.confirmation_token) {
            setError("Confirmation token is required");
            return;
        }

        if (!formData.current_password) {
            setError("Current password is required");
            return;
        }

        setLoading(true);
        try {
            const response = await clientFetcher({
                request: "auth/email/confirm",
                method: "POST",
                payload: {
                    confirmation_token: formData.confirmation_token,
                    current_password: formData.current_password,
                },
                token: session?.accessToken || "",
            });

            if (response.status === "success") {
                setError("");
                // Show success message
                setFormData({
                    new_email: "",
                    current_password: "",
                    email_token: "",
                    confirmation_token: "",
                });
                // Close dialog after a short delay
                setTimeout(() => {
                    setOpen(false);
                    setStep("initiate");
                    onSuccess?.();
                }, 2000);
            } else {
                setError(response.message || "Failed to confirm email update");
            }
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "An error occurred during confirmation"
            );
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setOpen(false);
        setStep("initiate");
        setFormData({
            new_email: "",
            current_password: "",
            email_token: "",
            confirmation_token: "",
        });
        setPendingEmail("");
        setError("");
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                    Update Email
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Update Email Address</DialogTitle>
                    <DialogDescription>
                        {step === "initiate" &&
                            "Verify your current password and enter your new email address"}
                        {step === "verify" &&
                            "Check your new email for the verification token"}
                        {step === "confirm" &&
                            "Check your current email for the confirmation link"}
                    </DialogDescription>
                </DialogHeader>

                {error && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {/* Step 1: Initiate Email Change */}
                {step === "initiate" && (
                    <form onSubmit={handleInitiate} className="space-y-4">
                        <div className="space-y-2">
                            <Label>Current Email</Label>
                            <Input value={currentEmail} disabled className="bg-muted" />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="new_email">New Email Address</Label>
                            <Input
                                id="new_email"
                                name="new_email"
                                type="email"
                                placeholder="Enter new email address"
                                value={formData.new_email}
                                onChange={handleInputChange}
                                disabled={loading}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="current_password">Current Password</Label>
                            <div className="relative">
                                <Input
                                    id="current_password"
                                    name="current_password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Enter current password"
                                    value={formData.current_password}
                                    onChange={handleInputChange}
                                    disabled={loading}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                                >
                                    {showPassword ? (
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
                                onClick={handleClose}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={loading}>
                                {loading ? "Verifying..." : "Continue"}
                            </Button>
                        </div>
                    </form>
                )}

                {/* Step 2: Verify New Email */}
                {step === "verify" && (
                    <form onSubmit={handleVerify} className="space-y-4">
                        <Alert className="border-blue-600 bg-blue-50">
                            <AlertCircle className="h-4 w-4 text-blue-600" />
                            <AlertDescription className="text-blue-800">
                                A verification link has been sent to{" "}
                                <strong>{pendingEmail}</strong>. Check your inbox for the
                                verification token.
                            </AlertDescription>
                        </Alert>

                        <div className="space-y-2">
                            <Label htmlFor="email_token">Verification Token</Label>
                            <Input
                                id="email_token"
                                name="email_token"
                                type="text"
                                placeholder="Paste the token from your email"
                                value={formData.email_token}
                                onChange={handleInputChange}
                                disabled={loading}
                                required
                            />
                        </div>

                        <div className="flex justify-end gap-2 pt-4">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => {
                                    setStep("initiate");
                                    setFormData({ ...formData, email_token: "" });
                                }}
                                disabled={loading}
                            >
                                Back
                            </Button>
                            <Button type="submit" disabled={loading}>
                                {loading ? "Verifying..." : "Continue"}
                            </Button>
                        </div>
                    </form>
                )}

                {/* Step 3: Confirm Email Update */}
                {step === "confirm" && (
                    <form onSubmit={handleConfirm} className="space-y-4">
                        <Alert className="border-blue-600 bg-blue-50">
                            <AlertCircle className="h-4 w-4 text-blue-600" />
                            <AlertDescription className="text-blue-800">
                                A confirmation link has been sent to{" "}
                                <strong>{currentEmail}</strong>. Check your inbox and paste the
                                confirmation token below.
                            </AlertDescription>
                        </Alert>

                        <div className="space-y-2">
                            <Label htmlFor="confirmation_token">Confirmation Token</Label>
                            <Input
                                id="confirmation_token"
                                name="confirmation_token"
                                type="text"
                                placeholder="Paste the confirmation token from your email"
                                value={formData.confirmation_token}
                                onChange={handleInputChange}
                                disabled={loading}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="confirm_password">Current Password</Label>
                            <div className="relative">
                                <Input
                                    id="confirm_password"
                                    name="current_password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Enter current password to confirm"
                                    value={formData.current_password}
                                    onChange={handleInputChange}
                                    disabled={loading}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                                >
                                    {showPassword ? (
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
                                onClick={() => {
                                    setStep("verify");
                                    setFormData({ ...formData, confirmation_token: "" });
                                }}
                                disabled={loading}
                            >
                                Back
                            </Button>
                            <Button type="submit" disabled={loading}>
                                {loading ? "Confirming..." : "Confirm Email Change"}
                            </Button>
                        </div>
                    </form>
                )}
            </DialogContent>
        </Dialog>
    );
}
