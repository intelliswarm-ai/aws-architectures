package ai.intelliswarm.inventory.controller;

import ai.intelliswarm.inventory.report.ReportService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.sf.jasperreports.engine.JRException;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/reports")
@RequiredArgsConstructor
@Slf4j
@PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
public class ReportController {

    private final ReportService reportService;

    @GetMapping(value = "/inventory/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> getInventoryReportPdf() throws JRException {
        log.info("GET /api/v1/reports/inventory/pdf");
        byte[] report = reportService.generateInventoryReportPdf();
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=inventory_report.pdf")
            .contentType(MediaType.APPLICATION_PDF)
            .body(report);
    }

    @GetMapping(value = "/inventory/excel", produces = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    public ResponseEntity<byte[]> getInventoryReportExcel() throws JRException {
        log.info("GET /api/v1/reports/inventory/excel");
        byte[] report = reportService.generateInventoryReportExcel();
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=inventory_report.xlsx")
            .body(report);
    }

    @GetMapping(value = "/low-stock/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> getLowStockReportPdf() throws JRException {
        log.info("GET /api/v1/reports/low-stock/pdf");
        byte[] report = reportService.generateLowStockReportPdf();
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=low_stock_report.pdf")
            .contentType(MediaType.APPLICATION_PDF)
            .body(report);
    }

    @PostMapping("/generate/{reportType}")
    public ResponseEntity<String> generateAndUploadReport(@PathVariable String reportType) throws JRException {
        log.info("POST /api/v1/reports/generate/{}", reportType);
        String s3Key = reportService.generateAndUploadReport(reportType);
        return ResponseEntity.ok("Report uploaded to: " + s3Key);
    }
}
