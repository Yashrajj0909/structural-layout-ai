/**
 * Column Grid Model Engine
 * Reuses 2D logic and adds dynamic 3D column generation
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── 2D Canvas Setup ──
    const canvas2d = document.getElementById('floorCanvas');
    const ctx2d = canvas2d.getContext('2d');
    const container2d = canvas2d.parentElement;

    // ── 3D Scene Setup ──
    const canvas3d = document.getElementById('threeCanvas');
    const renderer = new THREE.WebGLRenderer({ canvas: canvas3d, antialias: true });
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0D0F14);
    
    const camera = new THREE.PerspectiveCamera(45, canvas3d.clientWidth / canvas3d.clientHeight, 0.1, 1000);
    camera.position.set(20, 20, 20);
    camera.lookAt(0, 0, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    const gridHelper = new THREE.GridHelper(30, 30, 0x2A3040, 0x1A1F2B);
    scene.add(gridHelper);

    // State
    let rooms = [];
    let columns = [];
    let scale2d = 30;
    let offsetX = 0, offsetY = 0;
    let isDragging2d = false;
    let isDraggingRoom = false;
    let draggedRoom = null;
    let dragStartX, dragStartY;
    
    // ── UI Elements ──
    const colTypeSelect = document.getElementById('col-type');
    const colWidthInput = document.getElementById('col-width');
    const colDepthInput = document.getElementById('col-depth');
    const rectDepthRow = document.getElementById('rect-depth-row');
    const plotWidthInput = document.getElementById('plot-width');
    const plotLengthInput = document.getElementById('plot-length');
    const numBedInput = document.getElementById('num-bedrooms');
    const numBathInput = document.getElementById('num-bathrooms');
    const kitchenTypeSelect = document.getElementById('kitchen-type');
    const vastuCheckbox = document.getElementById('vastu-pref');
    const parkingCheckbox = document.getElementById('parking-req');
    const roadPosSelect = document.getElementById('road-pos');
    const roadDistSlider = document.getElementById('road-dist');
    const editModeCheckbox = document.getElementById('edit-mode');
    const btnUpdate = document.getElementById('btn-update');
    const btnResetView = document.getElementById('btn-reset-view');

    function init() {
        resize();
        updateModel();
        animate();
    }

    function resize() {
        // 2D
        canvas2d.width = container2d.clientWidth;
        canvas2d.height = container2d.clientHeight;
        offsetX = canvas2d.width / 2;
        offsetY = canvas2d.height / 2;

        // 3D
        renderer.setSize(canvas3d.clientWidth, canvas3d.clientHeight, false);
        camera.aspect = canvas3d.clientWidth / canvas3d.clientHeight;
        camera.updateProjectionMatrix();
    }

    function updateModel() {
        const W = parseFloat(plotWidthInput.value);
        const L = parseFloat(plotLengthInput.value);
        
        generateLayout(W, L);
        render2d();
        render3d(W, L);
    }

    function generateLayout(W, L) {
        const numBed = parseInt(numBedInput.value);
        const hasParking = parkingCheckbox.checked;

        rooms = [];
        const setback = 1.0;
        const uW = W - 2 * setback;
        const uL = L - 2 * setback;
        const originX = -W/2 + setback;
        const originY = -L/2 + setback;

        const isVertical = uL > uW;
        
        if (!isVertical) {
            const publicW = uW * 0.4;
            const serviceW = uW * 0.25;
            const privateW = uW - publicW - serviceW;

            rooms.push({ type: 'Entrance', name: 'Entry', x: originX, y: originY, w: publicW, h: uL * 0.15, color: '#F8FAFC', texture: 'tiles' });
            rooms.push({ type: 'Hall', name: 'Living Hall', x: originX, y: originY + uL * 0.15, w: publicW, h: uL * 0.85, color: '#FDFCF0', texture: 'wood' });
            rooms.push({ type: 'Dining', name: 'Dining', x: originX + publicW, y: originY, w: serviceW, h: uL * 0.4, color: '#FFF7ED', texture: 'tiles' });
            rooms.push({ type: 'Kitchen', name: 'Kitchen', x: originX + publicW, y: originY + uL * 0.4, w: serviceW, h: uL * 0.4, color: '#F0FDFA', texture: 'tiles' });
            rooms.push({ type: 'Toilet', name: 'Common Bath', x: originX + publicW, y: originY + uL * 0.8, w: serviceW, h: uL * 0.2, color: '#FEF2F2', texture: 'tiles' });

            const bedH = uL / numBed;
            for (let i = 0; i < numBed; i++) {
                rooms.push({ type: 'Bedroom', name: i === 0 ? 'Master' : `Bed ${i+1}`, x: originX + publicW + serviceW, y: originY + (i * bedH), w: privateW, h: bedH, color: '#F0FDF4', texture: 'wood' });
            }
        } else {
            const publicH = uL * 0.35;
            const serviceH = uL * 0.25;
            const privateH = uL - publicH - serviceH;

            rooms.push({ type: 'Hall', name: 'Living Hall', x: originX, y: originY, w: uW, h: publicH, color: '#FDFCF0', texture: 'wood' });
            rooms.push({ type: 'Kitchen', name: 'Kitchen', x: originX, y: originY + publicH, w: uW * 0.5, h: serviceH, color: '#F0FDFA', texture: 'tiles' });
            rooms.push({ type: 'Dining', name: 'Dining', x: originX + uW * 0.5, y: originY + publicH, w: uW * 0.5, h: serviceH, color: '#FFF7ED', texture: 'tiles' });

            const cols = numBed > 2 ? 2 : 1;
            const rows = Math.ceil(numBed / cols);
            const bW = uW / cols;
            const bH = privateH / rows;
            for (let i = 0; i < numBed; i++) {
                const r = Math.floor(i / cols);
                const c = i % cols;
                rooms.push({ type: 'Bedroom', name: `Bed ${i+1}`, x: originX + (c * bW), y: originY + publicH + serviceH + (r * bH), w: bW, h: bH, color: '#F0FDF4', texture: 'wood' });
            }
        }

        if (hasParking) {
            rooms.push({ type: 'Parking', name: 'Parking', x: -W/2, y: -L/2, w: setback, h: L, color: '#F1F5F9', texture: 'dots' });
        }

        calculateColumns();
    }

    function calculateColumns() {
        const xPoints = new Set();
        const yPoints = new Set();
        const snap = 0.1; // 10cm snapping threshold

        rooms.forEach(room => {
            // Round to nearest 0.1m to avoid double columns from precision errors
            const rx = Math.round(room.x / snap) * snap;
            const ry = Math.round(room.y / snap) * snap;
            const rw = Math.round(room.w / snap) * snap;
            const rh = Math.round(room.h / snap) * snap;

            xPoints.add(Number(rx.toFixed(2)));
            xPoints.add(Number((rx + rw).toFixed(2)));
            yPoints.add(Number(ry.toFixed(2)));
            yPoints.add(Number((ry + rh).toFixed(2)));
        });

        const sortedX = Array.from(xPoints).sort((a, b) => a - b);
        const sortedY = Array.from(yPoints).sort((a, b) => a - b);

        // Final filtering to ensure no two points are within snap distance
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

    function render2d() {
        ctx2d.clearRect(0, 0, canvas2d.width, canvas2d.height);
        
        const W = parseFloat(plotWidthInput.value);
        const L = parseFloat(plotLengthInput.value);
        const px = offsetX - (W/2)*scale2d;
        const py = offsetY - (L/2)*scale2d;
        const pw = W * scale2d;
        const ph = L * scale2d;

        drawRoad2d();

        // Draw Plot Boundary
        ctx2d.strokeStyle = 'rgba(245, 240, 232, 0.15)';
        ctx2d.setLineDash([5, 5]);
        ctx2d.strokeRect(px, py, pw, ph);
        ctx2d.setLineDash([]);

        // Draw Rooms
        rooms.forEach(r => {
            const rx = offsetX + r.x * scale2d;
            const ry = offsetY + r.y * scale2d;
            const rw = r.w * scale2d;
            const rh = r.h * scale2d;

            ctx2d.fillStyle = r.color;
            ctx2d.globalAlpha = 0.3;
            ctx2d.fillRect(rx, ry, rw, rh);
            ctx2d.globalAlpha = 1.0;
            ctx2d.strokeStyle = 'rgba(61, 90, 108, 0.3)';
            ctx2d.lineWidth = 1;
            ctx2d.strokeRect(rx, ry, rw, rh);

            ctx2d.fillStyle = 'rgba(245, 240, 232, 0.5)';
            ctx2d.font = '500 9px DM Mono';
            ctx2d.textAlign = 'center';
            ctx2d.fillText(r.name.toUpperCase(), rx + rw/2, ry + rh/2);
        });

        // ── DRAW STRUCTURAL GRID (BEAMS) ──
        const xPoints = [...new Set(columns.map(c => c.x))].sort((a,b) => a-b);
        const yPoints = [...new Set(columns.map(c => c.y))].sort((a,b) => a-b);

        ctx2d.strokeStyle = 'rgba(181, 101, 29, 0.4)';
        ctx2d.lineWidth = 2;
        ctx2d.setLineDash([5, 5]);

        xPoints.forEach(x => {
            ctx2d.beginPath();
            ctx2d.moveTo(offsetX + x * scale2d, offsetY + yPoints[0] * scale2d);
            ctx2d.lineTo(offsetX + x * scale2d, offsetY + yPoints[yPoints.length - 1] * scale2d);
            ctx2d.stroke();
        });

        yPoints.forEach(y => {
            ctx2d.beginPath();
            ctx2d.moveTo(offsetX + xPoints[0] * scale2d, offsetY + y * scale2d);
            ctx2d.lineTo(offsetX + xPoints[xPoints.length - 1] * scale2d, offsetY + y * scale2d);
            ctx2d.stroke();
        });
        ctx2d.setLineDash([]);

        // ── DRAW COLUMNS ──
        const type = colTypeSelect.value;
        const width = parseFloat(colWidthInput.value) / 1000;
        const depth = parseFloat(colDepthInput.value) / 1000;
        
        columns.forEach(c => {
            const cx = offsetX + c.x * scale2d;
            const cy = offsetY + c.y * scale2d;
            const cw = width * scale2d;
            const cd = (type === 'rectangle' ? depth : width) * scale2d;

            ctx2d.fillStyle = '#B5651D';
            if (type === 'circular') {
                ctx2d.beginPath();
                ctx2d.arc(cx, cy, cw/2, 0, Math.PI * 2);
                ctx2d.fill();
            } else {
                ctx2d.fillRect(cx - cw/2, cy - cd/2, cw, cd);
            }
        });

        // ── DRAW DIMENSIONS ──
        ctx2d.fillStyle = '#B5651D';
        ctx2d.font = '10px DM Mono';
        ctx2d.fillText(`${W}m`, offsetX, py - 10);
        ctx2d.save();
        ctx2d.translate(px - 15, offsetY);
        ctx2d.rotate(-Math.PI/2);
        ctx2d.fillText(`${L}m`, 0, 0);
        ctx2d.restore();

        drawDirectionSymbols2d(px, py, pw, ph);

        if (editModeCheckbox.checked) {
            ctx2d.fillStyle = 'rgba(181, 101, 29, 0.1)';
            ctx2d.fillRect(0, 0, canvas2d.width, 30);
            ctx2d.fillStyle = '#B5651D';
            ctx2d.font = 'bold 12px Barlow';
            ctx2d.textAlign = 'center';
            ctx2d.fillText('MANUAL EDIT MODE ACTIVE', canvas2d.width/2, 20);
        }
    }

    function drawDirectionSymbols2d(px, py, pw, ph) {
        const cx = 60;
        const cy = canvas2d.height - 60;
        const size = 20;

        ctx2d.save();
        ctx2d.translate(cx, cy);
        
        ctx2d.fillStyle = '#B5651D';
        ctx2d.font = 'bold 11px DM Mono';
        ctx2d.textAlign = 'center';
        ctx2d.textBaseline = 'middle';

        // Draw crosshair
        ctx2d.strokeStyle = 'rgba(181, 101, 29, 0.2)';
        ctx2d.lineWidth = 1;
        ctx2d.beginPath();
        ctx2d.moveTo(-size, 0); ctx2d.lineTo(size, 0);
        ctx2d.moveTo(0, -size); ctx2d.lineTo(0, size);
        ctx2d.stroke();

        // Labels
        ctx2d.fillText('N', 0, -size - 8);
        ctx2d.fillText('S', 0, size + 8);
        ctx2d.fillText('E', size + 10, 0);
        ctx2d.fillText('W', -size - 10, 0);

        ctx2d.restore();
    }

    function drawRoad2d() {
        const roadPos = roadPosSelect.value;
        const roadDist = parseFloat(roadDistSlider.value);
        if (roadPos === 'none') return;

        const W = parseFloat(plotWidthInput.value);
        const L = parseFloat(plotLengthInput.value);
        const roadWidth = 6 * scale2d;
        const distPx = roadDist * scale2d;
        
        ctx2d.fillStyle = 'rgba(245, 245, 245, 0.05)';
        const px = offsetX - (W/2)*scale2d;
        const py = offsetY - (L/2)*scale2d;
        const pw = W * scale2d;
        const ph = L * scale2d;

        if (roadPos === 'north') ctx2d.fillRect(px - 100, py - roadWidth - distPx, pw + 200, roadWidth);
        else if (roadPos === 'south') ctx2d.fillRect(px - 100, py + ph + distPx, pw + 200, roadWidth);
        else if (roadPos === 'west') ctx2d.fillRect(px - roadWidth - distPx, py - 100, roadWidth, ph + 200);
        else if (roadPos === 'east') ctx2d.fillRect(px + pw + distPx, py - 100, roadWidth, ph + 200);
    }

    function render3d(W, L) {
        // Clear previous 3D objects
        while(scene.children.length > 3) {
            const obj = scene.children[scene.children.length - 1];
            if(obj.geometry) obj.geometry.dispose();
            if(obj.material) obj.material.dispose();
            scene.remove(obj);
        }

        const type = colTypeSelect.value;
        const width = parseFloat(colWidthInput.value) / 1000;
        const depth = parseFloat(colDepthInput.value) / 1000;
        const height = 3.2;

        const colMat = new THREE.MeshLambertMaterial({ color: 0x3D5A6C });
        const beamMat = new THREE.MeshLambertMaterial({ color: 0x8B5E2A });
        const footingMat = new THREE.MeshLambertMaterial({ color: 0x444444 });

        columns.forEach(c => {
            let geom;
            if (type === 'circular') geom = new THREE.CylinderGeometry(width/2, width/2, height, 32);
            else if (type === 'square') geom = new THREE.BoxGeometry(width, height, width);
            else geom = new THREE.BoxGeometry(width, height, depth);

            const col = new THREE.Mesh(geom, colMat);
            col.position.set(c.x, height/2, c.y); // Note: 2D y is 3D z
            scene.add(col);

            const footing = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.4, 1.2), footingMat);
            footing.position.set(c.x, -0.2, c.y);
            scene.add(footing);
        });

        // Beams
        const xPoints = [...new Set(columns.map(c => c.x))].sort((a,b) => a-b);
        const yPoints = [...new Set(columns.map(c => c.y))].sort((a,b) => a-b);

        xPoints.forEach(x => {
            for(let i=0; i<yPoints.length-1; i++) {
                const span = yPoints[i+1] - yPoints[i];
                const beam = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.4, span), beamMat);
                beam.position.set(x, height - 0.2, (yPoints[i] + yPoints[i+1])/2);
                scene.add(beam);
            }
        });
        yPoints.forEach(y => {
            for(let i=0; i<xPoints.length-1; i++) {
                const span = xPoints[i+1] - xPoints[i];
                const beam = new THREE.Mesh(new THREE.BoxGeometry(span, 0.4, 0.25), beamMat);
                beam.position.set((xPoints[i] + xPoints[i+1])/2, height - 0.2, y);
                scene.add(beam);
            }
        });

        const plinth = new THREE.Mesh(new THREE.BoxGeometry(W, 0.2, L), new THREE.MeshLambertMaterial({ color: 0x1A1F2B }));
        plinth.position.set(0, -0.01, 0);
        scene.add(plinth);
    }

    function animate() {
        requestAnimationFrame(animate);
        if (!isDragging3d) scene.rotation.y += 0.002;
        renderer.render(scene, camera);
    }

    // ── Interactivity ──
    let isDragging3d = false;
    let lastMouseX, lastMouseY;

    canvas2d.addEventListener('mousedown', e => {
        const rect = canvas2d.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        if (editModeCheckbox.checked) {
            let found = null;
            for (let room of rooms) {
                const rx = offsetX + room.x * scale2d;
                const ry = offsetY + room.y * scale2d;
                const rw = room.w * scale2d;
                const rh = room.h * scale2d;
                if (mx >= rx && mx <= rx + rw && my >= ry && my <= ry + rh) {
                    found = room; break;
                }
            }
            if (found) {
                isDraggingRoom = true;
                draggedRoom = found;
                dragStartX = (mx - offsetX) / scale2d - found.x;
                dragStartY = (my - offsetY) / scale2d - found.y;
                return;
            }
        }
        isDragging2d = true;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
    });

    window.addEventListener('mousemove', e => {
        if (isDraggingRoom && draggedRoom) {
            const rect = canvas2d.getBoundingClientRect();
            draggedRoom.x = (e.clientX - rect.left - offsetX) / scale2d - dragStartX;
            draggedRoom.y = (e.clientY - rect.top - offsetY) / scale2d - dragStartY;
            calculateColumns();
            render2d();
            render3d(parseFloat(plotWidthInput.value), parseFloat(plotLengthInput.value));
            return;
        }
        if (isDragging2d) {
            offsetX += e.clientX - lastMouseX;
            offsetY += e.clientY - lastMouseY;
            lastMouseX = e.clientX; lastMouseY = e.clientY;
            render2d();
        }
    });

    window.addEventListener('mouseup', () => {
        isDragging2d = false;
        isDraggingRoom = false;
        draggedRoom = null;
    });

    canvas3d.addEventListener('mousedown', e => {
        isDragging3d = true;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
    });

    window.addEventListener('mousemove', e => {
        if (!isDragging3d) return;
        scene.rotation.y += (e.clientX - lastMouseX) * 0.01;
        scene.rotation.x += (e.clientY - lastMouseY) * 0.01;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
    });

    window.addEventListener('mouseup', () => isDragging3d = false);

    [plotWidthInput, plotLengthInput, numBedInput, numBathInput, kitchenTypeSelect, vastuCheckbox, parkingCheckbox, roadPosSelect, roadDistSlider, colTypeSelect, colWidthInput, colDepthInput].forEach(el => {
        el.addEventListener('input', () => {
            if (el === roadDistSlider) document.getElementById('dist-val').textContent = `${roadDistSlider.value}m`;
            if (el === colTypeSelect) rectDepthRow.style.display = el.value === 'rectangle' ? 'block' : 'none';
            updateModel();
        });
    });

    btnUpdate.addEventListener('click', updateModel);
    btnResetView.addEventListener('click', () => {
        scene.rotation.set(0,0,0);
        camera.position.set(20, 20, 20);
        camera.lookAt(0, 0, 0);
    });

    window.addEventListener('resize', resize);
    init();
});
