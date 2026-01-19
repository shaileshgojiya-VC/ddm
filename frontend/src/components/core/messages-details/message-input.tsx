"use client";

import { useState, useRef } from "react";
import { Paperclip, Send } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { validateFileSize } from "@/utils/file-upload";
import AttachmentPreview from "./attachment-preview";

export default function MessageInput() {
  const [message, setMessage] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = async () => {
    if (!message.trim() && !attachment) return;

    try {
      // Future: Implement send message API call
      // const formData = new FormData();
      // formData.append('message', message);
      // if (attachment) {
      //   formData.append('file', attachment);
      // }
      // await sendMessageAPI(formData);

      console.log("Sending message:", {
        text: message,
        attachment: attachment ? attachment.name : null,
      });

      // Reset form
      setMessage("");
      setAttachment(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      toast.success("Message sent successfully");
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAttachmentClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validation = validateFileSize(file);
    if (!validation.isValid) {
      toast.error("File too large", {
        description: validation.error,
      });
      return;
    }

    setAttachment(file);
    toast.success("File attached", {
      description: file.name,
    });
  };

  const handleRemoveAttachment = () => {
    setAttachment(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="p-4 space-y-3">
      {/* Attachment Preview */}
      {attachment && (
        <AttachmentPreview
          file={attachment}
          onRemove={handleRemoveAttachment}
        />
      )}

      {/* Message Input */}
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          className="hidden"
          accept="*/*"
        />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={handleAttachmentClick}
          className="shrink-0 size-11"
        >
          <Paperclip className="size-5" />
        </Button>
        <Input
          type="text"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          className="flex-1"
        />
        <Button
          type="button"
          size="icon"
          onClick={handleSend}
          disabled={!message.trim() && !attachment}
          className="shrink-0 size-11"
        >
          <Send className="size-5" />
        </Button>
      </div>
    </div>
  );
}
