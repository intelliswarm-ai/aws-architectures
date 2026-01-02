package ai.intelliswarm.inventory.report;

import ai.intelliswarm.inventory.model.Product;
import ai.intelliswarm.inventory.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.sf.jasperreports.engine.*;
import net.sf.jasperreports.engine.data.JRBeanCollectionDataSource;
import net.sf.jasperreports.engine.export.ooxml.JRXlsxExporter;
import net.sf.jasperreports.export.SimpleExporterInput;
import net.sf.jasperreports.export.SimpleOutputStreamExporterOutput;
import net.sf.jasperreports.export.SimpleXlsxReportConfiguration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Service for generating JasperReports.
 * Generates PDF and Excel reports for inventory data.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ReportService {

    private final ProductRepository productRepository;
    private final S3Client s3Client;

    private static final String REPORTS_BUCKET = System.getenv("S3_BUCKET_REPORTS");

    public byte[] generateInventoryReportPdf() throws JRException {
        log.info("Generating inventory report PDF");

        List<Product> products = productRepository.findAll();
        JRBeanCollectionDataSource dataSource = new JRBeanCollectionDataSource(products);

        Map<String, Object> parameters = createReportParameters("Inventory Report");
        parameters.put("totalValue", productRepository.calculateTotalInventoryValue());
        parameters.put("reorderCount", productRepository.countProductsNeedingReorder());

        JasperPrint jasperPrint = fillReport("inventory_report", parameters, dataSource);

        byte[] pdfBytes = JasperExportManager.exportReportToPdf(jasperPrint);
        log.info("Generated inventory report PDF: {} bytes", pdfBytes.length);

        return pdfBytes;
    }

    public byte[] generateInventoryReportExcel() throws JRException {
        log.info("Generating inventory report Excel");

        List<Product> products = productRepository.findAll();
        JRBeanCollectionDataSource dataSource = new JRBeanCollectionDataSource(products);

        Map<String, Object> parameters = createReportParameters("Inventory Report");
        JasperPrint jasperPrint = fillReport("inventory_report", parameters, dataSource);

        return exportToExcel(jasperPrint);
    }

    public byte[] generateLowStockReportPdf() throws JRException {
        log.info("Generating low stock report PDF");

        List<Product> products = productRepository.findProductsNeedingReorder();
        JRBeanCollectionDataSource dataSource = new JRBeanCollectionDataSource(products);

        Map<String, Object> parameters = createReportParameters("Low Stock Report");
        parameters.put("productCount", products.size());

        JasperPrint jasperPrint = fillReport("low_stock_report", parameters, dataSource);

        return JasperExportManager.exportReportToPdf(jasperPrint);
    }

    public String generateAndUploadReport(String reportType) throws JRException {
        byte[] reportBytes;
        String extension;

        switch (reportType.toLowerCase()) {
            case "inventory_pdf" -> {
                reportBytes = generateInventoryReportPdf();
                extension = ".pdf";
            }
            case "inventory_excel" -> {
                reportBytes = generateInventoryReportExcel();
                extension = ".xlsx";
            }
            case "low_stock" -> {
                reportBytes = generateLowStockReportPdf();
                extension = ".pdf";
            }
            default -> throw new IllegalArgumentException("Unknown report type: " + reportType);
        }

        String key = generateS3Key(reportType, extension);
        uploadToS3(key, reportBytes, extension.equals(".pdf") ? "application/pdf" :
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");

        log.info("Uploaded report to S3: {}", key);
        return key;
    }

    private JasperPrint fillReport(String reportName, Map<String, Object> parameters,
                                    JRBeanCollectionDataSource dataSource) throws JRException {
        try {
            InputStream reportStream = new ClassPathResource("reports/" + reportName + ".jasper").getInputStream();
            return JasperFillManager.fillReport(reportStream, parameters, dataSource);
        } catch (Exception e) {
            log.warn("Compiled report not found, compiling from JRXML: {}", reportName);
            try {
                InputStream jrxmlStream = new ClassPathResource("reports/" + reportName + ".jrxml").getInputStream();
                JasperReport jasperReport = JasperCompileManager.compileReport(jrxmlStream);
                return JasperFillManager.fillReport(jasperReport, parameters, dataSource);
            } catch (Exception ex) {
                throw new JRException("Failed to load report: " + reportName, ex);
            }
        }
    }

    private Map<String, Object> createReportParameters(String title) {
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("reportTitle", title);
        parameters.put("generatedAt", LocalDateTime.now());
        parameters.put("generatedBy", "Inventory Management System");
        parameters.put("companyName", "IntelliSwarm AI");
        return parameters;
    }

    private byte[] exportToExcel(JasperPrint jasperPrint) throws JRException {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        JRXlsxExporter exporter = new JRXlsxExporter();
        exporter.setExporterInput(new SimpleExporterInput(jasperPrint));
        exporter.setExporterOutput(new SimpleOutputStreamExporterOutput(outputStream));

        SimpleXlsxReportConfiguration configuration = new SimpleXlsxReportConfiguration();
        configuration.setOnePagePerSheet(false);
        configuration.setRemoveEmptySpaceBetweenRows(true);
        configuration.setDetectCellType(true);
        exporter.setConfiguration(configuration);

        exporter.exportReport();
        return outputStream.toByteArray();
    }

    private String generateS3Key(String reportType, String extension) {
        String date = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HHmmss"));
        return String.format("reports/%s/%s_%s%s", date, reportType, timestamp, extension);
    }

    private void uploadToS3(String key, byte[] content, String contentType) {
        if (REPORTS_BUCKET == null || REPORTS_BUCKET.isEmpty()) {
            log.warn("S3 bucket not configured, skipping upload");
            return;
        }

        PutObjectRequest request = PutObjectRequest.builder()
            .bucket(REPORTS_BUCKET)
            .key(key)
            .contentType(contentType)
            .build();

        s3Client.putObject(request, RequestBody.fromBytes(content));
    }
}
