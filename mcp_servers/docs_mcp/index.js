const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Setup logging directory
const LOG_DIR = path.join(__dirname, '..', '..', 'logs');
fs.mkdirSync(LOG_DIR, { recursive: true });

function log(msg) {
  fs.appendFileSync(path.join(LOG_DIR, 'docs_mcp.log'), `${new Date().toISOString()} - ${msg}\n`);
}

log("Google Docs MCP Server starting...");

// Setup mock document directory
const DOCS_DIR = path.join(LOG_DIR, 'workspace_docs');
fs.mkdirSync(DOCS_DIR, { recursive: true });

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
          name: "docs-mcp",
          version: "1.0.0"
        }
      };
    } else if (request.method === 'tools/list') {
      response.result = {
        tools: [
          {
            name: "append_dated_pulse_report",
            description: "Appends or replaces a dated weekly product review pulse report in a Google Doc. Supports idempotency via anchor headers.",
            inputSchema: {
              type: "object",
              properties: {
                document_title: {
                  type: "string",
                  description: "Title of the running Google Doc (e.g., 'Weekly Review Pulse — Groww')"
                },
                iso_week: {
                  type: "string",
                  description: "Target ISO week (e.g., '2026-W24')"
                },
                report_markdown: {
                  type: "string",
                  description: "Markdown content of the weekly report to append or replace"
                }
              },
              required: ["document_title", "iso_week", "report_markdown"]
            }
          }
        ]
      };
    } else if (request.method === 'tools/call') {
      const toolName = request.params.name;
      const args = request.params.arguments;
      
      if (toolName === 'append_dated_pulse_report') {
        const resultText = handleAppendReport(args.document_title, args.iso_week, args.report_markdown);
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

function handleAppendReport(title, isoWeek, markdown) {
  log(`Executing append_dated_pulse_report for ${title} (${isoWeek})`);
  
  // Normalizing title for local mock filename
  const filename = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
  const filePath = path.join(DOCS_DIR, filename);
  
  const headingAnchor = `pulse-anchor-${isoWeek}`;
  const datedHeading = `## Week ${isoWeek.split('-W')[1]} (Period: Last 8-12 weeks) <!-- ${headingAnchor} -->`;
  
  let docContent = "";
  if (fs.existsSync(filePath)) {
    docContent = fs.readFileSync(filePath, 'utf-8');
  } else {
    docContent = `# ${title}\n\nThis is a running log of weekly product review pulses.\n\n`;
  }
  
  // Check if anchor already exists (Idempotency check)
  const anchorIndex = docContent.indexOf(headingAnchor);
  
  if (anchorIndex !== -1) {
    log(`Anchor ${headingAnchor} found. Replacing existing section (Idempotency mode).`);
    // Locate the heading line containing the anchor
    const lines = docContent.split('\n');
    let startLineIdx = -1;
    let endLineIdx = -1;
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(headingAnchor)) {
        startLineIdx = i;
        // Search for next heading section starting with "## Week" or end of document
        for (let j = i + 1; j < lines.length; j++) {
          if (lines[j].startsWith('## Week')) {
            endLineIdx = j;
            break;
          }
        }
        break;
      }
    }
    
    if (startLineIdx !== -1) {
      if (endLineIdx === -1) endLineIdx = lines.length;
      
      const newSection = `${datedHeading}\n\n${markdown}\n`;
      lines.splice(startLineIdx, endLineIdx - startLineIdx, newSection);
      docContent = lines.join('\n');
    }
  } else {
    log(`Anchor ${headingAnchor} not found. Appending new section (Append mode).`);
    // Append a page break equivalent and the new section
    docContent += `\n---\n\n${datedHeading}\n\n${markdown}\n`;
  }
  
  fs.writeFileSync(filePath, docContent, 'utf-8');
  
  const mockUrl = `https://docs.google.com/document/d/mock_groww_doc_id/edit#heading=${headingAnchor}`;
  log(`Document successfully updated at: ${filePath}`);
  
  return JSON.stringify({
    status: "success",
    message: "Dated report successfully updated in the running document.",
    filepath: filePath,
    document_url: mockUrl,
    header_anchor_id: headingAnchor
  });
}
