/**
 * 2D Floor Plan Generator Engine
 * StructAI Designer
 */

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('floorCanvas');
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('canvas-container');
    const infoPanel = document.getElementById('info-panel');
    const toast = document.getElementById('toast');

    // State
    let rooms = [];
    let columns = [];
    let scale = 40; // pixels per meter
    let offsetX = 0;
    let offsetY = 0;
    let isDragging = false;
    let isDraggingRoom = false;
    let draggedRoom = null;
    let lastX, lastY;
    let hoveredRoom = null;
    let dragStartX, dragStartY;
    let builtBounds = { x: 0, y: 0, w: 0, h: 0 };
    let plotWarning = "";

    // UI Elements
    const btnGen = document.getElementById('btn-generate');
    const btnReset = document.getElementById('btn-reset');
    const btnDownload = document.getElementById('btn-download');
    const roadPosSelect = document.getElementById('road-pos');
    const roadDistSlider = document.getElementById('road-dist');
    const editModeCheckbox = document.getElementById('edit-mode');
    const showColumnsCheckbox = document.getElementById('show-columns');
    const colTypeSelect = document.getElementById('col-type');
    const colWidthInput = document.getElementById('col-width');
    const colDepthInput = document.getElementById('col-depth');
    const rectDepthRow = document.getElementById('rect-depth-row');
    const btnToggleHeader = document.getElementById('btn-toggle-columns-header');

    // Initial Setup
    function init() {
        resizeCanvas();
        generateLayout();
        // Sync header button state
        if (showColumnsCheckbox.checked) {
            btnToggleHeader.style.background = 'rgba(181, 101, 29, 0.2)';
            btnToggleHeader.style.borderColor = 'var(--copper)';
            btnToggleHeader.style.color = 'var(--copper)';
        }
        render();
    }

    function resizeCanvas() {
        const container = document.getElementById('canvas-container');
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
        
        // Auto-fit scaling
        const W_ft = parseFloat(document.getElementById('plot-width').value) || 25;
        const L_ft = parseFloat(document.getElementById('plot-length').value) || 40;
        const padding = 60;
        const availableW = canvas.width - padding;
        const availableH = canvas.height - padding;
        
        // Convert feet to meters for internal calc
        const W_m = W_ft * 0.3048;
        const L_m = L_ft * 0.3048;
        
        scale = Math.min(availableW / W_m, availableH / L_m);
        offsetX = canvas.width / 2;
        offsetY = canvas.height / 2;
    }

    function generateLayout() {
        const ft_to_m = 0.3048;
        const W_ft = parseFloat(document.getElementById('plot-width').value);
        const L_ft = parseFloat(document.getElementById('plot-length').value);
        const numBed = parseInt(document.getElementById('num-bedrooms').value);
        const numBath = parseInt(document.getElementById('num-bathrooms').value);

        // Minimum Plot Size Check (25ft x 40ft)
        const minW_ft = 25;
        const minL_ft = 40;
        
        rooms = [];
        columns = [];
        
        if (W_ft < minW_ft || L_ft < minL_ft) {
            plotWarning = "Invalid plot size:\nMinimum required is 25 ft width × 40 ft length\nfor a proper Vastu-compliant 2D house plan.";
            render();
            return;
        }
        
        plotWarning = "";
        
        // Define Usable Area
        // On a 25ft plot, setbacks must be minimal to fit standard 12ft and 10ft rooms
        const W = W_ft * ft_to_m;
        const L = L_ft * ft_to_m;
        const setback = W_ft <= 30 ? 0.1 : 0.5; // Minimal setback for 25-30ft plots
        const uW = W - 2 * setback;
        const uL = L - 2 * setback;
        const originX = -W/2 + setback;
        const originY = -L/2 + setback;
        builtBounds = { x: originX, y: originY, w: uW, h: uL };

        // Generate Layout following Indian Vastu Principles & Strict Dimensions
        generateVastuModernLayout(originX, originY, uW, uL, numBed, numBath);

        calculateColumns();
        resizeCanvas(); // Ensure scale fits the new design
        render();

        document.getElementById('total-area').textContent = `${(W_ft * L_ft).toFixed(1)} sq.ft`;
        document.getElementById('built-area').textContent = `${(W_ft * L_ft * 0.85).toFixed(1)} sq.ft`;
    }

    function generateVastuModernLayout(ox, oy, uw, ul, nBed, nBath) {
        const ft_to_m = 0.3048;
        
        // TARGET DIMENSIONS (Strictly as per User Input)
        const livingW = 12 * ft_to_m;
        const livingH = 16 * ft_to_m;
        const masterW = 12 * ft_to_m;
        const masterH = 12 * ft_to_m;
        const bed2W = 10 * ft_to_m;
        const bed2H = 12 * ft_to_m;
        const kitchenW = 8 * ft_to_m;
        const kitchenH = 10 * ft_to_m;
        const diningW = 10 * ft_to_m;
        const diningH = 10 * ft_to_m;
        const bathW = 5 * ft_to_m;
        const bathH = 8 * ft_to_m;
        const poojaW = 4 * ft_to_m;
        const poojaH = 6 * ft_to_m;
        const corridorW = 0.92; // 3ft

        // --- GRID PARTITIONING ---
        // For a 25ft plot (~7.6m), we use a West (12ft) | Corridor (3ft) | East (10ft) split
        // This exactly fits 12 + 3 + 10 = 25ft.
        
        const westW = masterW; 
        const centralX = ox + westW;
        const eastX = centralX + corridorW;
        const eastW = uw - westW - corridorW;

        // 1. NORTH-EAST (NE): Pooja Room & Entrance
        rooms.push({ type: 'Pooja', name: 'Pooja (4x6)', x: ox + uw - poojaW, y: oy, w: poojaW, h: poojaH, color: '#FFF7ED', texture: 'tiles', vastu: 'NE' });
        rooms.push({ type: 'Entrance', name: 'Main Entry', x: ox + uw - 2.5, y: oy + poojaH + 0.2, w: 2.5, h: 1.2, color: '#F8FAFC', texture: 'tiles' });

        // 2. NORTH/EAST: Living Room (12x16 ft)
        // Note: On a 25ft plot, Living Room takes the East Side (approx 10ft wide) and extends vertically
        rooms.push({ type: 'Hall', name: 'Living (12x16)', x: eastX, y: oy + poojaH + 1.6, w: Math.min(eastW, livingW), h: livingH, color: '#FDFCF0', texture: 'wood', vastu: 'E' });

        // 3. SOUTH-EAST (SE): Kitchen (8x10 ft)
        rooms.push({ type: 'Kitchen', name: 'Kitchen (8x10)', x: ox + uw - kitchenW, y: oy + ul - kitchenH, w: kitchenW, h: kitchenH, color: '#F0FDFA', texture: 'tiles', vastu: 'SE' });

        // 4. SOUTH-WEST (SW): Master Bedroom (12x12 ft)
        rooms.push({ type: 'Bedroom', name: 'Master Bed (12x12)', x: ox, y: oy + ul - masterH, w: masterW, h: masterH, color: '#F0FDF4', texture: 'wood', vastu: 'SW' });

        // 5. WEST / NORTH-WEST: Bedroom 2 (10x12 ft)
        rooms.push({ type: 'Bedroom', name: 'Bed 2 (10x12)', x: ox, y: oy + bathH + 0.5, w: bed2W, h: bed2H, color: '#F0FDF4', texture: 'wood', vastu: 'W' });

        // 6. WEST / NORTH-WEST: Bathrooms (5x8 ft)
        rooms.push({ type: 'Toilet', name: 'Bath (5x8)', x: ox, y: oy, w: bathW, h: bathH, color: '#FEF2F2', texture: 'tiles', vastu: 'NW' });
        
        // 7. DINING: Near Kitchen
        rooms.push({ type: 'Dining', name: 'Dining (10x10)', x: eastX, y: oy + ul - kitchenH - diningH - 0.2, w: Math.min(eastW, diningW), h: diningH, color: '#FFF7ED', texture: 'tiles' });

        // 8. CENTRAL CORRIDOR
        rooms.push({ type: 'Corridor', name: 'Corridor (3ft)', x: centralX, y: oy, w: corridorW, h: ul, color: '#F8FAFC', texture: 'tiles' });
    }

    function generateVastuLayout(ox, oy, uw, ul, nBed, nBath) {
        // VASTU GRID (3x3 approximate zoning)
        // NW (Bath) | N (Living) | NE (Pooja/Entry)
        // W (Bath/Din)| Center    | E (Dining/Entry)
        // SW (Master) | S (Stairs) | SE (Kitchen)
        
        const cellW = uw / 3;
        const cellH = ul / 3;

        // 1. Kitchen in South-East (SE)
        rooms.push({ 
            type: 'Kitchen', name: 'Kitchen (SE)', 
            x: ox + 2*cellW, y: oy + 2*cellH, w: cellW, h: cellH, 
            color: '#F0FDFA', texture: 'tiles', vastu: 'SE' 
        });

        // 2. Master Bedroom in South-West (SW)
        rooms.push({ 
            type: 'Bedroom', name: 'Master Bed (SW)', 
            x: ox, y: oy + 2*cellH, w: cellW, h: cellH, 
            color: '#F0FDF4', texture: 'wood', vastu: 'SW' 
        });

        // 3. Pooja Room in North-East (NE)
        rooms.push({ 
            type: 'Pooja', name: 'Pooja (NE)', 
            x: ox + 2*cellW, y: oy, w: cellW * 0.5, h: cellH * 0.5, 
            color: '#FFF7ED', texture: 'tiles', vastu: 'NE' 
        });

        // 4. Main Entrance in North/East (NE area)
        rooms.push({ 
            type: 'Entrance', name: 'Main Entry', 
            x: ox + 2*cellW + cellW * 0.5, y: oy, w: cellW * 0.5, h: cellH * 0.5, 
            color: '#F8FAFC', texture: 'tiles', vastu: 'NE' 
        });

        // 5. Living Room in North/East (N & Center-N area)
        rooms.push({ 
            type: 'Hall', name: 'Living Room', 
            x: ox + cellW, y: oy, w: cellW, h: cellH, 
            color: '#FDFCF0', texture: 'wood', vastu: 'N' 
        });

        // 6. Bathroom in North-West (NW)
        rooms.push({ 
            type: 'Toilet', name: 'Bath (NW)', 
            x: ox, y: oy, w: cellW, h: cellH * 0.6, 
            color: '#FEF2F2', texture: 'tiles', vastu: 'NW' 
        });

        // 7. Dining in East/West (Using East/Center-East)
        rooms.push({ 
            type: 'Dining', name: 'Dining', 
            x: ox + 2*cellW, y: oy + cellH, w: cellW, h: cellH, 
            color: '#FFF7ED', texture: 'tiles', vastu: 'E' 
        });

        // 8. Staircase in South-West (Shared with SW zone or South)
        // We'll place it in South zone to avoid overlapping Master Bed fully
        rooms.push({ 
            type: 'Stairs', name: 'Staircase (SW)', 
            x: ox + cellW, y: oy + 2*cellH, w: cellW, h: cellH, 
            color: '#F1F5F9', texture: 'stairs', vastu: 'S' 
        });

        // Additional Bedrooms if needed
        if (nBed > 1) {
            rooms.push({ 
                type: 'Bedroom', name: 'Bedroom 2', 
                x: ox, y: oy + cellH, w: cellW, h: cellH, 
                color: '#F0FDF4', texture: 'wood', vastu: 'W' 
            });
        }

        // Additional Bathrooms
        if (nBath > 1) {
            rooms.push({ 
                type: 'Toilet', name: 'Bath 2', 
                x: ox, y: oy + cellH * 0.6, w: cellW, h: cellH * 0.4, 
                color: '#FEF2F2', texture: 'tiles', vastu: 'NW' 
            });
        }
    }

    function calculateColumns() {
        // Collect all unique X and Y points from room corners to create a grid
        const xPoints = new Set();
        const yPoints = new Set();
        const snap = 0.1; // 10cm snapping threshold
        
        rooms.forEach(room => {
            // Round coordinates to avoid double columns due to floating point precision
            const rx = Math.round(room.x / snap) * snap;
            const ry = Math.round(room.y / snap) * snap;
            const rw = Math.round(room.w / snap) * snap;
            const rh = Math.round(room.h / snap) * snap;

            xPoints.add(Number(rx.toFixed(2)));
            xPoints.add(Number((rx + rw).toFixed(2)));
            yPoints.add(Number(ry.toFixed(2)));
            yPoints.add(Number((ry + rh).toFixed(2)));
        });

        // Filter out small differences (snapping)
        const sortedX = Array.from(xPoints).sort((a,b) => a-b);
        const sortedY = Array.from(yPoints).sort((a,b) => a-b);

        const filterPoints = (pts) => {
            if (pts.length === 0) return [];
            const filtered = [pts[0]];
            for (let i = 1; i < pts.length; i++) {
                if (pts[i] - filtered[filtered.length - 1] > snap) {
                    filtered.push(pts[i]);
                }
            }
            return filtered;
        };

        const finalX = filterPoints(sortedX);
        const finalY = filterPoints(sortedY);

        columns = [];
        finalX.forEach(x => {
            finalY.forEach(y => {
                columns.push({ x, y });
            });
        });
    }

    function render() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        drawRoad();
        drawGrid();

        const W = parseFloat(document.getElementById('plot-width').value);
        const L = parseFloat(document.getElementById('plot-length').value);
        const px = offsetX - (W/2)*scale;
        const py = offsetY - (L/2)*scale;
        const pw = W * scale;
        const ph = L * scale;

        ctx.fillStyle = '#F1F8F1'; 
        ctx.fillRect(px, py, pw, ph);
        drawLandscape(px, py, pw, ph);

        ctx.strokeStyle = '#D1D5DB';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(px, py, pw, ph);
        ctx.setLineDash([]);

        // Vastu Annotations (Underground NE, Overhead SW)
        if (rooms.length > 0) {
            drawVastuAnnotations(px, py, pw, ph);
        }

        rooms.forEach(room => {
            const rx = offsetX + room.x * scale;
            const ry = offsetY + room.y * scale;
            const rw = room.w * scale;
            const rh = room.h * scale;

            const isHovered = hoveredRoom === room;
            const isBeingDragged = draggedRoom === room;
            
            ctx.fillStyle = room.color;
            ctx.globalAlpha = (isHovered || isBeingDragged) ? 0.7 : 0.45;
            ctx.fillRect(rx, ry, rw, rh);
            ctx.globalAlpha = 1.0;

            drawTexture(rx, ry, rw, rh, room.texture);

            // WALL THICKNESS: External 12in (30cm), Internal 6in (15cm)
            // Draw walls based on room boundary
            const extWall = 0.3 * scale;
            const intWall = 0.15 * scale;
            
            ctx.strokeStyle = (isHovered || isBeingDragged) ? '#B5651D' : '#1F2937'; 
            ctx.lineWidth = intWall; // Default internal wall
            
            // Check if edges are "external" (at the boundary of buildable area)
            const isAtLeft = builtBounds && Math.abs(room.x - builtBounds.x) < 0.1;
            const isAtRight = builtBounds && Math.abs((room.x + room.w) - (builtBounds.x + builtBounds.w)) < 0.1;
            const isAtTop = builtBounds && Math.abs(room.y - builtBounds.y) < 0.1;
            const isAtBottom = builtBounds && Math.abs((room.y + room.h) - (builtBounds.y + builtBounds.h)) < 0.1;

            ctx.beginPath();
            // Top edge
            ctx.lineWidth = isAtTop ? extWall : intWall;
            ctx.moveTo(rx, ry); ctx.lineTo(rx + rw, ry);
            ctx.stroke();

            // Right edge
            ctx.beginPath();
            ctx.lineWidth = isAtRight ? extWall : intWall;
            ctx.moveTo(rx + rw, ry); ctx.lineTo(rx + rw, ry + rh);
            ctx.stroke();

            // Bottom edge
            ctx.beginPath();
            ctx.lineWidth = isAtBottom ? extWall : intWall;
            ctx.moveTo(rx + rw, ry + rh); ctx.lineTo(rx, ry + rh);
            ctx.stroke();

            // Left edge
            ctx.beginPath();
            ctx.lineWidth = isAtLeft ? extWall : intWall;
            ctx.moveTo(rx, ry + rh); ctx.lineTo(rx, ry);
            ctx.stroke();

            ctx.fillStyle = '#111827';
            ctx.font = `600 ${Math.max(11, scale/3.2)}px Barlow`;
            ctx.textAlign = 'center';
            ctx.fillText(room.name.toUpperCase(), rx + rw/2, ry + rh/2 - 5);
            
            const area = (room.w * room.h).toFixed(1);
            ctx.fillStyle = '#4B5563';
            ctx.font = `500 ${Math.max(9, scale/5)}px DM Mono`;
            ctx.fillText(`${area} m²`, rx + rw/2, ry + rh/2 + 12);

            // Safety Annotations: Fire Exit
            if (room.type === 'Kitchen' || (room.type === 'Hall' && isAtRight)) {
                ctx.fillStyle = '#EF4444';
                ctx.font = 'bold 9px Barlow';
                ctx.fillText('FIRE EXIT →', rx + rw - 30, ry + 15);
            }

            drawFurniture(rx, ry, rw, rh, room.type, room);
            if (room.type === 'Stairs') drawStairs(rx, ry, rw, rh);
            if (room.type === 'Toilet') drawToilet(rx, ry, rw, rh);
            drawOpenings(rx, ry, rw, rh, room.type, room);
            drawDimensions(rx, ry, rw, rh, room);
        });

        if (showColumnsCheckbox.checked) {
            drawColumns();
        }

        if (editModeCheckbox.checked) {
            drawEditModeOverlay();
        }

        if (plotWarning) {
            drawWarning();
        }

        // drawScaleIndicator(); // Not defined, removing to fix ReferenceError
        drawCompass();
    }

    function drawWarning() {
        ctx.fillStyle = 'rgba(239, 68, 68, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#EF4444';
        ctx.font = 'bold 24px Barlow';
        ctx.textAlign = 'center';
        
        const lines = plotWarning.split('\n');
        lines.forEach((line, i) => {
            ctx.fillText(line, canvas.width/2, canvas.height/2 + (i * 35));
        });
    }

    function drawColumns() {
        const type = colTypeSelect.value;
        const width = parseFloat(colWidthInput.value) / 1000; // mm to m
        const depth = parseFloat(colDepthInput.value) / 1000;
        
        // ── DRAW GRID LINES (BEAMS) ──
        const xPoints = [...new Set(columns.map(c => c.x))].sort((a,b) => a-b);
        const yPoints = [...new Set(columns.map(c => c.y))].sort((a,b) => a-b);

        ctx.strokeStyle = 'rgba(181, 101, 29, 0.2)'; // Fainter copper for beams
        ctx.lineWidth = 1.5;
        ctx.setLineDash([10, 5]);

        xPoints.forEach(x => {
            ctx.beginPath();
            ctx.moveTo(offsetX + x * scale, offsetY + yPoints[0] * scale);
            ctx.lineTo(offsetX + x * scale, offsetY + yPoints[yPoints.length - 1] * scale);
            ctx.stroke();
        });

        yPoints.forEach(y => {
            ctx.beginPath();
            ctx.moveTo(offsetX + xPoints[0] * scale, offsetY + y * scale);
            ctx.lineTo(offsetX + xPoints[xPoints.length - 1] * scale, offsetY + y * scale);
            ctx.stroke();
        });
        ctx.setLineDash([]);

        // ── DRAW COLUMNS (Matching Screenshot Aesthetic) ──
        columns.forEach(c => {
            const cx = offsetX + c.x * scale;
            const cy = offsetY + c.y * scale;
            const cw = width * scale;
            const cd = (type === 'rectangle' ? depth : width) * scale;

            if (type === 'circular') {
                // Outer Glow/Ring (Greenish like screenshot)
                ctx.fillStyle = 'rgba(16, 185, 129, 0.1)';
                ctx.beginPath();
                ctx.arc(cx, cy, cw * 1.2, 0, Math.PI * 2);
                ctx.fill();

                // Main Column
                ctx.strokeStyle = '#10B981'; // Greenish stroke
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(cx, cy, cw/2, 0, Math.PI * 2);
                ctx.stroke();

                // Inner Dot
                ctx.fillStyle = '#10B981';
                ctx.beginPath();
                ctx.arc(cx, cy, cw/6, 0, Math.PI * 2);
                ctx.fill();
            } else {
                // Square/Rectangle aesthetic
                ctx.fillStyle = 'rgba(181, 101, 29, 0.1)';
                ctx.fillRect(cx - (cw*1.2)/2, cy - (cd*1.2)/2, cw*1.2, cd*1.2);

                ctx.strokeStyle = '#B5651D';
                ctx.lineWidth = 2;
                ctx.strokeRect(cx - cw/2, cy - cd/2, cw, cd);

                ctx.fillStyle = '#B5651D';
                ctx.fillRect(cx - cw/6, cy - cd/6, cw/3, cd/3);
            }
        });
    }

    function drawEditModeOverlay() {
        ctx.fillStyle = 'rgba(181, 101, 29, 0.1)';
        ctx.fillRect(0, 0, canvas.width, 50);
        ctx.fillStyle = '#B5651D';
        ctx.font = 'bold 16px Barlow';
        ctx.textAlign = 'center';
        ctx.fillText('MANUAL EDIT MODE ACTIVE — DRAG ROOMS TO REPOSITION', canvas.width/2, 32);
    }

    function drawRoad() {
        const roadPos = roadPosSelect.value;
        const roadDist = parseFloat(roadDistSlider.value);
        if (roadPos === 'none') return;

        const W = parseFloat(document.getElementById('plot-width').value);
        const L = parseFloat(document.getElementById('plot-length').value);
        const roadWidth = 8 * scale;
        const roadColor = '#F1F5F9';
        
        ctx.save();
        ctx.fillStyle = roadColor;
        
        const px = offsetX - (W/2)*scale;
        const py = offsetY - (L/2)*scale;
        const pw = W * scale;
        const ph = L * scale;

        const distPx = roadDist * scale;

        if (roadPos === 'north') {
            ctx.fillRect(px - scale*20, py - roadWidth - distPx, pw + scale*40, roadWidth);
            drawRoadDetails(px - scale*20, py - roadWidth - distPx, pw + scale*40, roadWidth, 'h');
        } else if (roadPos === 'south') {
            ctx.fillRect(px - scale*20, py + ph + distPx, pw + scale*40, roadWidth);
            drawRoadDetails(px - scale*20, py + ph + distPx, pw + scale*40, roadWidth, 'h');
        } else if (roadPos === 'west') {
            ctx.fillRect(px - roadWidth - distPx, py - scale*20, roadWidth, ph + scale*40);
            drawRoadDetails(px - roadWidth - distPx, py - scale*20, roadWidth, ph + scale*40, 'v');
        } else if (roadPos === 'east') {
            ctx.fillRect(px + pw + distPx, py - scale*20, roadWidth, ph + scale*40);
            drawRoadDetails(px + pw + distPx, py - scale*20, roadWidth, ph + scale*40, 'v');
        }
        
        ctx.restore();
    }

    function drawRoadDetails(x, y, w, h, dir) {
        ctx.strokeStyle = '#CBD5E1';
        ctx.setLineDash([30, 30]);
        ctx.lineWidth = 2;
        ctx.beginPath();
        if (dir === 'h') {
            ctx.moveTo(x, y + h/2); ctx.lineTo(x + w, y + h/2);
        } else {
            ctx.moveTo(x + w/2, y); ctx.lineTo(x + w/2, y + h);
        }
        ctx.stroke();
        ctx.setLineDash([]);
        
        ctx.fillStyle = '#94A3B8';
        ctx.font = 'bold 14px Barlow';
        ctx.textAlign = 'center';
        if (dir === 'h') {
            ctx.fillText('PUBLIC ROAD', x + w/2, y + h/2 + 30);
        } else {
            ctx.save();
            ctx.translate(x + w/2 + 30, y + h/2);
            ctx.rotate(Math.PI/2);
            ctx.fillText('PUBLIC ROAD', 0, 0);
            ctx.restore();
        }
    }

    function drawCompass() {
        const cx = 80; // Move to top-left for better visibility in Vastu mode
        const cy = 80;
        const size = 40;

        ctx.save();
        
        // Background Circle (Subtle)
        ctx.beginPath();
        ctx.arc(cx, cy, size + 5, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.fill();
        ctx.strokeStyle = '#D1D5DB';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Cardinal Direction Labels (Fixed for Vastu)
        // North (Top), East (Right), South (Bottom), West (Left)
        ctx.fillStyle = '#111827';
        ctx.font = 'bold 14px Barlow';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        ctx.fillText('N', cx, cy - size + 5);
        ctx.font = '500 11px Barlow';
        ctx.fillText('S', cx, cy + size - 5);
        ctx.fillText('E', cx + size - 5, cy);
        ctx.fillText('W', cx - size + 5, cy);

        // Vastu Quadrant Labels (NW, NE, SW, SE)
        ctx.font = 'bold 9px Barlow';
        ctx.fillStyle = '#B5651D';
        ctx.fillText('NW', cx - size/1.5, cy - size/1.5);
        ctx.fillText('NE', cx + size/1.5, cy - size/1.5);
        ctx.fillText('SW', cx - size/1.5, cy + size/1.5);
        ctx.fillText('SE', cx + size/1.5, cy + size/1.5);

        // Compass Needle (North - Triangular)
        ctx.fillStyle = '#B5651D';
        ctx.beginPath();
        ctx.moveTo(cx, cy - size + 15);
        ctx.lineTo(cx - 6, cy);
        ctx.lineTo(cx + 6, cy);
        ctx.closePath();
        ctx.fill();

        // Compass Needle (South)
        ctx.fillStyle = '#1F2937';
        ctx.beginPath();
        ctx.moveTo(cx, cy + size - 15);
        ctx.lineTo(cx - 6, cy);
        ctx.lineTo(cx + 6, cy);
        ctx.closePath();
        ctx.fill();

        // Center Point
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(cx, cy, 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    }

    function drawLandscape(px, py, pw, ph) {
        const treeSize = 30;
        ctx.fillStyle = '#D1FAE5';
        ctx.strokeStyle = '#10B981';
        ctx.lineWidth = 1;
        
        [
            {x: px + 40, y: py + 40},
            {x: px + pw - 40, y: py + 40},
            {x: px + 40, y: py + ph - 40},
            {x: px + pw - 40, y: py + ph - 40}
        ].forEach(pos => {
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, treeSize/2, 0, Math.PI*2);
            ctx.fill();
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, treeSize/4, 0, Math.PI*2);
            ctx.stroke();
        });
    }

    function drawVastuAnnotations(px, py, pw, ph) {
        ctx.save();
        ctx.font = 'bold 9px DM Mono';
        ctx.textAlign = 'center';

        // NE: Underground Water Tank
        const neX = px + pw - 20;
        const neY = py + 20;
        ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
        ctx.beginPath();
        ctx.arc(neX, neY, 12, 0, Math.PI*2);
        ctx.fill();
        ctx.strokeStyle = '#3B82F6';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = '#3B82F6';
        ctx.fillText('UG TANK', neX, neY + 4);

        // SW: Overhead Water Tank
        const swX = px + 20;
        const swY = py + ph - 20;
        ctx.fillStyle = 'rgba(181, 101, 29, 0.1)';
        ctx.beginPath();
        ctx.arc(swX, swY, 12, 0, Math.PI*2);
        ctx.fill();
        ctx.strokeStyle = '#B5651D';
        ctx.stroke();
        ctx.fillStyle = '#B5651D';
        ctx.fillText('OH TANK', swX, swY + 4);

        ctx.restore();
    }

    function drawTexture(x, y, w, h, type) {
        if (!type) return;
        ctx.save();
        ctx.beginPath();
        ctx.rect(x, y, w, h);
        ctx.clip();
        
        ctx.strokeStyle = 'rgba(0,0,0,0.03)';
        ctx.lineWidth = 1;

        if (type === 'tiles') {
            const gap = 15;
            for (let i = x % gap; i < x + w; i += gap) {
                ctx.beginPath(); ctx.moveTo(i, y); ctx.lineTo(i, y + h); ctx.stroke();
            }
            for (let i = y % gap; i < y + h; i += gap) {
                ctx.beginPath(); ctx.moveTo(x, i); ctx.lineTo(x + w, i); ctx.stroke();
            }
        } else if (type === 'wood') {
            const gap = 10;
            for (let i = x % gap; i < x + w; i += gap) {
                ctx.beginPath(); ctx.moveTo(i, y); ctx.lineTo(i, y + h); ctx.stroke();
            }
        } else if (type === 'stairs') {
            const gap = 8;
            for (let i = y; i < y + h; i += gap) {
                ctx.beginPath(); ctx.moveTo(x, i); ctx.lineTo(x + w, i); ctx.stroke();
            }
            ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + w, y + h); ctx.stroke();
        } else if (type === 'dots') {
            const gap = 10;
            for (let i = x; i < x + w; i += gap) {
                for (let j = y; j < y + h; j += gap) {
                    ctx.beginPath(); ctx.arc(i, j, 0.5, 0, Math.PI*2); ctx.fill();
                }
            }
        }
        ctx.restore();
    }

    function drawDimensions(x, y, w, h, room) {
        ctx.strokeStyle = '#9CA3AF';
        ctx.lineWidth = 1;
        ctx.fillStyle = '#6B7280';
        ctx.font = '9px DM Mono';
        const offset = 20;
        const ft_to_m = 0.3048;

        ctx.beginPath();
        ctx.moveTo(x, y + h + offset); ctx.lineTo(x + w, y + h + offset);
        ctx.moveTo(x, y + h + offset - 4); ctx.lineTo(x, y + h + offset + 4);
        ctx.moveTo(x + w, y + h + offset - 4); ctx.lineTo(x + w, y + h + offset + 4);
        ctx.stroke();
        ctx.textAlign = 'center';
        ctx.fillText(`${(room.w / ft_to_m).toFixed(0)}ft`, x + w/2, y + h + offset + 12);

        ctx.save();
        ctx.translate(x + w + offset, y + h/2);
        ctx.rotate(Math.PI/2);
        ctx.beginPath();
        ctx.moveTo(-h/2, 0); ctx.lineTo(h/2, 0);
        ctx.moveTo(-h/2, -4); ctx.lineTo(-h/2, 4);
        ctx.moveTo(h/2, -4); ctx.lineTo(h/2, 4);
        ctx.stroke();
        ctx.textAlign = 'center';
        ctx.fillText(`${(room.h / ft_to_m).toFixed(0)}ft`, 0, 12);
        ctx.restore();
    }

    function drawFurniture(x, y, w, h, type, room) {
        ctx.save();
        ctx.strokeStyle = 'rgba(55, 65, 81, 0.4)';
        ctx.lineWidth = 1.2;
        
        if (type === 'Bedroom') {
            // Bed (Standard Double)
            const bedW = 1.8 * scale;
            const bedH = 2.0 * scale;
            const bx = x + (w - bedW)/2;
            const by = y + 10;
            ctx.strokeRect(bx, by, bedW, bedH);
            // Pillows
            ctx.strokeRect(bx + 15, by + 5, (bedW/2) - 20, 15);
            ctx.strokeRect(bx + (bedW/2) + 5, by + 5, (bedW/2) - 20, 15);
            // Wardrobe
            ctx.strokeRect(x + 5, y + h - 25, w - 10, 20);
        } else if (type === 'Hall') {
            // Sofa set (L-shape)
            ctx.beginPath();
            ctx.moveTo(x + 30, y + 30);
            ctx.lineTo(x + w - 40, y + 30);
            ctx.lineTo(x + w - 40, y + 100);
            ctx.stroke();
            // Coffee table
            ctx.strokeRect(x + 50, y + 50, w - 100, 30);
        } else if (type === 'Dining') {
            // Table
            const tw = 1.2 * scale;
            const th = 1.2 * scale;
            const tx = x + (w - tw)/2;
            const ty = y + (h - th)/2;
            ctx.strokeRect(tx, ty, tw, th);
            // Chairs
            for (let i = 0; i < 4; i++) {
                const angle = (i * Math.PI) / 2;
                const cx = tx + tw/2 + Math.cos(angle) * (tw/2 + 10);
                const cy = ty + th/2 + Math.sin(angle) * (th/2 + 10);
                ctx.strokeRect(cx - 10, cy - 10, 20, 20);
            }
        } else if (type === 'Kitchen') {
            // Platform (L-shape)
            ctx.strokeRect(x + 5, y + 5, w - 10, 25);
            // Sink
            ctx.strokeRect(x + 15, y + 8, 20, 15);
            // Stove
            const sx = x + w - 40;
            const sy = y + 10;
            ctx.beginPath(); ctx.arc(sx + 10, sy + 8, 5, 0, Math.PI*2); ctx.stroke();
            ctx.beginPath(); ctx.arc(sx + 25, sy + 8, 5, 0, Math.PI*2); ctx.stroke();
            
            if (room && room.vastu === 'SE') {
                ctx.fillStyle = '#B5651D';
                ctx.font = 'bold 9px Barlow';
                ctx.fillText('COOKING (EAST) →', x + 10, y + 45);
            }
        }
        ctx.restore();
    }

    function drawStairs(x, y, w, h) {
        const stepH = h / 10;
        ctx.strokeStyle = '#94A3B8';
        for (let i = 0; i < 10; i++) {
            ctx.strokeRect(x + 5, y + i * stepH, w - 10, stepH);
        }
        // Clockwise indicator
        ctx.beginPath();
        ctx.arc(x + w/2, y + h/2, Math.min(w, h) * 0.3, 0, Math.PI * 1.5);
        ctx.stroke();
        // Arrow head
        ctx.fillText('↻ CLOCKWISE', x + w/2, y + h/2);
    }
    function drawToilet(x, y, w, h) {
        const cx = x + w/2;
        const cy = y + 20;
        // Commode
        ctx.beginPath(); ctx.ellipse(cx, cy, 8, 12, 0, 0, Math.PI*2); ctx.stroke();
        ctx.strokeRect(cx - 10, cy - 18, 20, 6);
        // Shower area
        ctx.strokeRect(x + 5, y + h - 30, w - 10, 25);
        ctx.beginPath(); ctx.moveTo(x+5, y+h-30); ctx.lineTo(x+w-5, y+h-5); ctx.stroke();
    }

    function drawGrid() {
        ctx.strokeStyle = 'rgba(243, 244, 246, 0.5)';
        ctx.lineWidth = 0.5;
        const step = scale; 
        
        for (let x = offsetX % step; x < canvas.width; x += step) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
        }
        for (let y = offsetY % step; y < canvas.height; y += step) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
        }
    }

    function drawOpenings(x, y, w, h, type, room) {
        const wallThick = 6;
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#FFFFFF';

        if (['Bedroom', 'Hall', 'Kitchen'].includes(type)) {
            const winW = w * 0.4;
            const wx = x + (w - winW)/2;
            ctx.clearRect(wx, y + h - wallThick/2 - 1, winW, wallThick + 2);
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(wx, y + h - wallThick/2 - 1, winW, wallThick + 2);
            ctx.strokeStyle = '#3D5A6C';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(wx, y + h); ctx.lineTo(wx + winW, y + h);
            ctx.moveTo(wx, y + h - 3); ctx.lineTo(wx + winW, y + h - 3);
            ctx.stroke();

            // Vastu: Extra windows on North/East for ventilation
            if (room.vastu === 'NE' || room.vastu === 'N' || room.vastu === 'E') {
                const winW2 = w * 0.3;
                const wx2 = x + 10;
                ctx.clearRect(wx2, y - wallThick/2 - 1, winW2, wallThick + 2);
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(wx2, y - wallThick/2 - 1, winW2, wallThick + 2);
                ctx.strokeStyle = '#3D5A6C';
                ctx.beginPath();
                ctx.moveTo(wx2, y); ctx.lineTo(wx2 + winW2, y);
                ctx.moveTo(wx2, y + 3); ctx.lineTo(wx2 + winW2, y + 3);
                ctx.stroke();
            }
        }

        ctx.lineWidth = 1.5;
        ctx.strokeStyle = '#374151';
        const doorSize = scale * 0.9;

        if (type === 'Hall' || type === 'Bedroom') {
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(x + 10, y - wallThick/2 - 1, doorSize, wallThick + 2);
            drawDoor(x + 10, y, doorSize, 'top');
        } else if (type === 'Toilet') {
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(x - wallThick/2 - 1, y + 10, wallThick + 2, doorSize);
            drawDoor(x, y + 10, doorSize, 'left');
        }
    }

    function drawDoor(x, y, size, side) {
        ctx.save();
        ctx.beginPath();
        if (side === 'bottom') {
            ctx.arc(x, y, size, -Math.PI/2, 0);
            ctx.moveTo(x, y); ctx.lineTo(x, y - size);
        } else if (side === 'top') {
            ctx.arc(x, y, size, 0, Math.PI/2);
            ctx.moveTo(x, y); ctx.lineTo(x + size, y);
        } else if (side === 'left') {
            ctx.arc(x, y, size, -Math.PI/2, 0);
            ctx.moveTo(x, y); ctx.lineTo(x, y - size);
        } else if (side === 'right') {
            ctx.arc(x, y, size, Math.PI/2, Math.PI);
            ctx.moveTo(x, y); ctx.lineTo(x - size, y);
        }
        ctx.stroke();
        ctx.restore();
    }

    // Interactivity
    canvas.addEventListener('mousedown', e => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        if (editModeCheckbox.checked) {
            // Find room to drag
            let found = null;
            for (let i = rooms.length - 1; i >= 0; i--) {
                const room = rooms[i];
                const rx = offsetX + room.x * scale;
                const ry = offsetY + room.y * scale;
                const rw = room.w * scale;
                const rh = room.h * scale;

                if (mouseX >= rx && mouseX <= rx + rw && mouseY >= ry && mouseY <= ry + rh) {
                    found = room;
                    break;
                }
            }

            if (found) {
                isDraggingRoom = true;
                draggedRoom = found;
                dragStartX = (mouseX - offsetX) / scale - found.x;
                dragStartY = (mouseY - offsetY) / scale - found.y;
                canvas.style.cursor = 'grabbing';
                return;
            }
        }

        isDragging = true;
        lastX = e.clientX;
        lastY = e.clientY;
        canvas.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', e => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        if (isDraggingRoom && draggedRoom) {
            draggedRoom.x = (mouseX - offsetX) / scale - dragStartX;
            draggedRoom.y = (mouseY - offsetY) / scale - dragStartY;
            calculateColumns();
            render();
            return;
        }

        if (isDragging) {
            offsetX += e.clientX - lastX;
            offsetY += e.clientY - lastY;
            lastX = e.clientX;
            lastY = e.clientY;
            render();
        } else {
            // Hover detection
            let found = null;
            for (let room of rooms) {
                const rx = offsetX + room.x * scale;
                const ry = offsetY + room.y * scale;
                const rw = room.w * scale;
                const rh = room.h * scale;

                if (mouseX >= rx && mouseX <= rx + rw && mouseY >= ry && mouseY <= ry + rh) {
                    found = room;
                    break;
                }
            }

            if (found !== hoveredRoom) {
                hoveredRoom = found;
                if (found) {
                    canvas.style.cursor = editModeCheckbox.checked ? 'move' : 'pointer';
                    showInfo(found);
                } else {
                    canvas.style.cursor = 'grab';
                    infoPanel.style.display = 'none';
                }
                render();
            }
        }
    });

    window.addEventListener('mouseup', () => {
        isDragging = false;
        isDraggingRoom = false;
        draggedRoom = null;
        canvas.style.cursor = 'grab';
    });

    roadPosSelect.addEventListener('change', render);
    roadDistSlider.addEventListener('input', () => {
        document.getElementById('dist-val').textContent = `${roadDistSlider.value}m`;
        render();
    });
    editModeCheckbox.addEventListener('change', render);
    showColumnsCheckbox.addEventListener('change', () => {
        if (showColumnsCheckbox.checked) {
            btnToggleHeader.style.background = 'rgba(181, 101, 29, 0.2)';
            btnToggleHeader.style.borderColor = 'var(--copper)';
            btnToggleHeader.style.color = 'var(--copper)';
        } else {
            btnToggleHeader.style.background = 'transparent';
            btnToggleHeader.style.borderColor = 'var(--border)';
            btnToggleHeader.style.color = 'var(--sand)';
        }
        render();
    });
    colTypeSelect.addEventListener('change', () => {
        rectDepthRow.style.display = colTypeSelect.value === 'rectangle' ? 'block' : 'none';
        render();
    });
    colWidthInput.addEventListener('input', render);
    colDepthInput.addEventListener('input', render);

    btnToggleHeader.addEventListener('click', () => {
        showColumnsCheckbox.checked = !showColumnsCheckbox.checked;
        if (showColumnsCheckbox.checked) {
            btnToggleHeader.style.background = 'rgba(181, 101, 29, 0.2)';
            btnToggleHeader.style.borderColor = 'var(--copper)';
            btnToggleHeader.style.color = 'var(--copper)';
        } else {
            btnToggleHeader.style.background = 'transparent';
            btnToggleHeader.style.borderColor = 'var(--border)';
            btnToggleHeader.style.color = 'var(--sand)';
        }
        render();
    });

    function showInfo(room) {
        infoPanel.style.display = 'block';
        document.getElementById('room-type').textContent = room.name;
        document.getElementById('room-dim').textContent = `${room.w.toFixed(1)} × ${room.h.toFixed(1)}m`;
        document.getElementById('room-area').textContent = `${(room.w * room.h).toFixed(1)} m²`;
    }

    window.zoom = (factor) => {
        scale *= factor;
        render();
    };

    window.resetZoom = () => {
        scale = 40;
        offsetX = canvas.width / 2;
        offsetY = canvas.height / 2;
        render();
    };

    btnGen.addEventListener('click', () => {
        toast.classList.add('show');
        generateLayout();
        render();
        setTimeout(() => toast.classList.remove('show'), 2000);
    });

    btnReset.addEventListener('click', () => {
        document.getElementById('plot-width').value = 12;
        document.getElementById('plot-length').value = 15;
        document.getElementById('num-bedrooms').value = 2;
        document.getElementById('num-bathrooms').value = 2;
        roadPosSelect.value = 'none';
        editModeCheckbox.checked = false;
        init();
    });

    btnDownload.addEventListener('click', () => {
        const link = document.createElement('a');
        link.download = 'floorplan-structai.png';
        link.href = canvas.toDataURL();
        link.click();
    });

    init();
});
