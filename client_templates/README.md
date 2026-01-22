# Client Engagement Email Templates

Place your HTML email templates here. These templates are sent to individual clients
based on which Varicon modules they're NOT using.

## Required Template Files

Copy your HTML templates to this folder:

```
client_templates/
├── timesheet.html         # For clients not using Timesheets
├── claims.html            # For clients not using Claims
├── deliveryDocket.html    # For clients not using Delivery Dockets
├── siteDiary.html         # For clients not using Site Diaries
├── purchaseOrder.html     # For clients not using Purchase Orders
├── variations.html        # For clients not using Variations
├── accountPayable.html    # For clients not using Bills
└── projectInvitation.html # General project invitation
```

## How It Works

1. After the CS team receives the risk analysis report
2. The system checks each high/medium risk client
3. For each client, it looks at which modules they're NOT using
4. It randomly selects one matching template and sends it
5. If no template matches their unused modules, no email is sent

## Module to Template Mapping

| Varicon Module     | Template File          |
|--------------------|------------------------|
| Timesheets         | timesheet.html         |
| Claims             | claims.html            |
| Delivery Dockets   | deliveryDocket.html    |
| Site Diaries       | siteDiary.html         |
| Purchase Orders    | purchaseOrder.html     |
| Variations         | variations.html        |
| Bills              | accountPayable.html    |
| Projects           | projectInvitation.html |

## Testing

For testing, all emails are sent to the `EMAIL_RECEIVER` in your `.env` file.
In production, you would modify this to send to actual client emails.

