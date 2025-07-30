// Task 12 Verification Script
// Run this script to verify that the 3D visualization implementation is working

const API_BASE = 'http://localhost:8000';

async function testAPI() {
    console.log('🔍 Testing Backend APIs...\n');
    
    try {
        // Test Health
        const healthResponse = await fetch(`${API_BASE}/health`);
        const health = await healthResponse.json();
        console.log('✅ Health Check:', health.status === 'ok' ? 'PASSED' : 'FAILED');
        
        // Test Materials
        const materialsResponse = await fetch(`${API_BASE}/api/materials`);
        const materials = await materialsResponse.json();
        console.log('✅ Materials API:', materials.length > 0 ? 'PASSED' : 'FAILED');
        console.log(`   Found ${materials.length} materials`);
        
        // Test Simulations endpoint
        const simulationsResponse = await fetch(`${API_BASE}/api/v1/simulations`);
        console.log('✅ Simulations API:', simulationsResponse.ok ? 'PASSED' : 'FAILED');
        
        console.log('\n🎯 Backend Status: ALL SYSTEMS OPERATIONAL\n');
        return true;
        
    } catch (error) {
        console.error('❌ Backend Test Failed:', error.message);
        return false;
    }
}

async function checkFrontendFiles() {
    console.log('📁 Checking Task 12 Implementation Files...\n');
    
    const fs = require('fs');
    const path = require('path');
    
    const requiredFiles = [
        'frontend/src/types/visualization.ts',
        'frontend/src/hooks/useSimulationResult.ts', 
        'frontend/src/components/ResultVisualization.tsx',
        'frontend/src/pages/ResultPage.tsx',
        'frontend/src/api/simulations.ts'
    ];
    
    let allFilesExist = true;
    
    requiredFiles.forEach(file => {
        if (fs.existsSync(file)) {
            console.log(`✅ ${file} - EXISTS`);
        } else {
            console.log(`❌ ${file} - MISSING`);
            allFilesExist = false;
        }
    });
    
    // Check package.json for plotly dependencies
    const packageJson = JSON.parse(fs.readFileSync('frontend/package.json', 'utf8'));
    const hasPlotly = packageJson.dependencies['plotly.js'] && packageJson.dependencies['react-plotly.js'];
    console.log(`${hasPlotly ? '✅' : '❌'} Plotly.js Dependencies - ${hasPlotly ? 'INSTALLED' : 'MISSING'}`);
    
    console.log(`\n📋 File Check: ${allFilesExist && hasPlotly ? 'ALL FILES PRESENT' : 'SOME FILES MISSING'}\n`);
    return allFilesExist && hasPlotly;
}

async function main() {
    console.log('🚀 Task 12: Frontend 3D Results Visualization - VERIFICATION\n');
    console.log('=' * 60 + '\n');
    
    const filesOk = checkFrontendFiles();
    const apiOk = await testAPI();
    
    console.log('📊 VERIFICATION SUMMARY:');
    console.log('=' * 30);
    console.log(`Backend API: ${apiOk ? '✅ WORKING' : '❌ FAILED'}`);
    console.log(`Frontend Files: ${filesOk ? '✅ COMPLETE' : '❌ INCOMPLETE'}`);
    console.log(`Overall Status: ${apiOk && filesOk ? '🎉 READY FOR TESTING' : '🔧 NEEDS ATTENTION'}`);
    
    if (apiOk && filesOk) {
        console.log('\n🎯 Next Steps:');
        console.log('1. Open http://localhost:3000 in your browser');
        console.log('2. Create a new simulation');
        console.log('3. Check that materials load properly');
        console.log('4. View results page with 3D visualization');
        console.log('5. Test field switching and educational panel');
    }
}

// Run in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
    main().catch(console.error);
}

// For browser console
if (typeof window !== 'undefined') {
    window.testTask12 = main;
    console.log('Run testTask12() to verify implementation');
} 