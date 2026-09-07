import os
import mimetypes
from email.mime.base import MIMEBase
from email import encoders

def create_attachment(file_path):
    """
    Loads a file and creates a base64 encoded MIME base attachment object.
    Raises FileNotFoundError if the file doesn't exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Attachment file not found at: {file_path}")
        
    file_name = os.path.basename(file_path)
    
    # Guess the content type of the file
    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
        
    main_type, sub_type = content_type.split('/', 1)
    
    # Load and encode attachment payload
    try:
        with open(file_path, 'rb') as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
            
        encoders.encode_base64(attachment)
        
        # Add content disposition headers
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=file_name
        )
        return attachment
    except Exception as e:
        print(f"[Attachment Handler] Error packing attachment: {e}")
        raise e
