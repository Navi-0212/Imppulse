const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Setup logging directory
const LOG_DIR = path.join(__dirname, '..', '..', 'logs');
const EMAILS_DIR = path.join(LOG_DIR, 'sent_emails');
fs.mkdirSync(LOG_DIR, { recursive: true });
fs.mkdirSync(EMAILS_DIR, { recursive: true });

const HISTORY_FILE = path.join(LOG_DIR, 'delivery_history.json');

function log(msg) {
  fs.appendFileSync(path.join(LOG_DIR, 'gmail_mcp.log'), `${new Date().toISOString()} - ${msg}\n`);
}

log("Gmail MCP Server starting...");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', (line) => {
  if (!line.trim()) return;
  
  try {
    const request = JSON.parse(line);
    log(`Received: ${request.method} (ID: ${request.id})`);
    
    let response = {
      jsonrpc: "2.0",
      id: request.id
    };
    
    if (request.method === 'initialize') {
      response.result = {
        protocolVersion: "2024-11-05",
        capabilities: {
          tools: {}
        },
        serverInfo: {
          name: "gmail-mcp",
          version: "1.0.0"
        }
      };
    } else if (request.method === 'tools/list') {
      response.result = {
        tools: [
          {
            name: "send_pulse_teaser_notification",
            description: "Sends a stakeholder email notification summarizing the top themes and linking to the full Google Doc report.",
            inputSchema: {
              type: "object",
              properties: {
                recipient_emails: {
                  type: "array",
                  items: { type: "string" },
                  description: "List of stakeholder email addresses"
                },
                subject: {
                  type: "string",
                  description: "Email subject line"
                },
                product_name: {
                  type: "string",
                  description: "Product being reported (e.g. 'Groww')"
                },
                iso_week: {
                  type: "string",
                  description: "Target ISO week (e.g., '2026-W24')"
                },
                top_themes: {
                  type: "array",
                  items: { type: "string" },
                  description: "Bulleted list of top 3 teaser themes"
                },
                google_doc_url: {
                  type: "string",
                  description: "URL of the Google Doc containing the full report"
                },
                header_anchor_id: {
                  type: "string",
                  description: "Google Doc heading anchor tag (e.g., 'pulse-anchor-2026-W24')"
                }
              },
              required: ["recipient_emails", "subject", "product_name", "iso_week", "top_themes", "google_doc_url", "header_anchor_id"]
            }
          }
        ]
      };
    } else if (request.method === 'tools/call') {
      const toolName = request.params.name;
      const args = request.params.arguments;
      
      if (toolName === 'send_pulse_teaser_notification') {
        const resultText = handleSendEmail(args);
        response.result = {
          content: [
            {
              type: "text",
              text: resultText
            }
          ]
        };
      } else {
        response.error = {
          code: -32601,
          message: `Method not found: ${toolName}`
        };
      }
    } else {
      response.result = {};
    }
    
    process.stdout.write(JSON.stringify(response) + "\n");
    
  } catch (err) {
    log(`Error handling request: ${err.message}`);
  }
});

function handleSendEmail(args) {
  log(`Executing send_pulse_teaser_notification for ${args.product_name} (${args.iso_week})`);
  
  // Read history to check if already sent (Idempotency Check)
  let history = [];
  if (fs.existsSync(HISTORY_FILE)) {
    try {
      history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf-8'));
    } catch (e) {
      log(`Failed reading history file: ${e.message}`);
    }
  }
  
  const alreadySent = history.some(run => 
    run.product === args.product_name && 
    run.iso_week === args.iso_week && 
    run.type === "email_sent"
  );
  
  if (alreadySent) {
    log(`Teaser email already sent for ${args.product_name} ${args.iso_week}. Skipping.`);
    return JSON.stringify({
      status: "skipped",
      reason: "Email already dispatched for this target ISO week and product. Idempotency enforced.",
      message_id: "skipped_duplicate"
    });
  }
  
  // Construct email body
  const docDeepLink = `${args.google_doc_url}#heading=${args.header_anchor_id}`;
  const bulletPoints = args.top_themes.map(t => `- ${t}`).join('\n');
  
  const emailContent = `From: impullse-weekly@groww-analytics.internal
To: ${args.recipient_emails.join(', ')}
Subject: ${args.subject}
Date: ${new Date().toUTCString()}

Hi Team,

Here is your Weekly Review Pulse teaser for ${args.product_name} (${args.iso_week}):

Top Sentiment Themes:
${bulletPoints}

Read the full grounding-compliant report containing verbatim customer quotes and actionable product ideas on Google Docs:
👉 ${docDeepLink}

Best regards,
Impullse Automation Engine
`;

  // Save email to local mock mail spool
  const emailFilename = `email_${args.product_name.toLowerCase()}_${args.iso_week}.txt`;
  const emailPath = path.join(EMAILS_DIR, emailFilename);
  fs.writeFileSync(emailPath, emailContent, 'utf-8');
  log(`Email drafted and saved locally to: ${emailPath}`);
  
  // Save to history log
  history.push({
    timestamp: new Date().toISOString(),
    product: args.product_name,
    iso_week: args.iso_week,
    type: "email_sent",
    recipients: args.recipient_emails,
    email_file: emailPath
  });
  
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2), 'utf-8');
  
  const mockMsgId = `gmail_mock_${Date.now()}`;
  log(`Email dispatch completed. Message ID: ${mockMsgId}`);
  
  return JSON.stringify({
    status: "success",
    message: "Teaser email notification successfully delivered.",
    message_id: mockMsgId,
    email_path: emailPath
  });
}
